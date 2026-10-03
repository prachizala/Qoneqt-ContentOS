import os
import uuid
import logging
import socket
import redis
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models.models import (
    Project, Script, Scene, Video, QAResult, Publication, ProjectStatus
)
from backend.app.schemas.project import (
    ContentRequestCreate,
    ContentRequestResponse,
    ProjectDetailResponse,
    ScriptResponse,
    SceneResponse,
    VideoResponse,
    QAResultResponse,
    PublicationResponse
)
from backend.app.services.regeneration_service import SceneRegenerationService
from backend.app.services.subscription_service import SubscriptionService
from workers.tasks import pipeline_orchestrator, run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects Pipeline"])

def is_celery_redis_available() -> bool:
    """Checks if Redis server is reachable for Celery dispatch."""
    if os.getenv("USE_MOCK_AI", "false").lower() in ("true", "1") or os.getenv("ENVIRONMENT") == "test":
        return False
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    if "redis:6379" in redis_url or "//redis" in redis_url:
        try:
            socket.gethostbyname("redis")
        except Exception:
            return False
    try:
        client = redis.Redis.from_url(redis_url, socket_timeout=0.5, socket_connect_timeout=0.5)
        return bool(client.ping())
    except Exception:
        return False

@router.post("", response_model=ContentRequestResponse, status_code=status.HTTP_201_CREATED)
@router.post("/generate-pipeline", response_model=ContentRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ContentRequestCreate,
    background_tasks: BackgroundTasks,
    execution_mode: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default="default_user", alias="X-User-Id"),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new video project entry after verifying subscription tier limits for the authenticated Clerk user,
    then triggers the asynchronous or synchronous pipeline orchestrator.
    """
    # 1. Enforce Subscription Tier Limits for Clerk userId (Free: 2/month, Creator: 15/month, Pro: 50/month, Enterprise: Unlimited)
    resolved_user_id = x_user_id if isinstance(x_user_id, str) and x_user_id else "default_user"
    await SubscriptionService.enforce_video_generation_limit(db, user_id=resolved_user_id)

    try:
        resolved_tone = request.tone or request.hookStyle or request.objective or "Viral / Hook Driven"
        resolved_style = request.visualStyle or request.style or "cinematic"

        project = Project(
            id=uuid.uuid4(),
            topic=request.topic,
            objective=resolved_tone,
            audience=request.audience,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            language=request.language,
            style=resolved_style,
            status=ProjectStatus.DRAFT
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
    except Exception as e:
        logger.error(f"Failed to create project in database: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating project: {str(e)}"
        )

    project_id_str = str(project.id)
    mode = (execution_mode or os.getenv("EXECUTION_MODE", "async")).lower()
    logger.info(f"Project created with ID {project_id_str} in mode '{mode}'. Launching pipeline task...")

    try:
        if mode == "sync":
            background_tasks.add_task(run_pipeline, project_id_str)
        elif is_celery_redis_available():
            try:
                pipeline_orchestrator.delay(project_id_str)
            except Exception as exc:
                logger.warning(f"Celery dispatch failed ({exc}). Falling back to FastAPI BackgroundTasks.")
                background_tasks.add_task(run_pipeline, project_id_str)
        else:
            logger.info("Celery/Redis unavailable. Running pipeline via FastAPI BackgroundTasks.")
            background_tasks.add_task(run_pipeline, project_id_str)
    except Exception as bg_err:
        logger.error(f"Failed to launch background pipeline for project {project_id_str}: {bg_err}", exc_info=True)

    return project

@router.post("/{project_id}/run-sync")
async def run_project_sync(project_id: uuid.UUID):
    """
    Executes pipeline synchronously for debugging and terminal log inspection.
    """
    project_id_str = str(project_id)
    await run_pipeline(project_id_str)
    return {"status": "completed", "project_id": project_id_str}

@router.get("", response_model=List[ContentRequestResponse])
async def list_projects(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated list of video generation projects.
    """
    offset = (page - 1) * limit
    stmt = select(Project).order_by(Project.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return projects

@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project_detail(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns complete project details including script, scenes, video assets, and QA status.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.script),
            selectinload(Project.scenes),
            selectinload(Project.videos),
            selectinload(Project.qa_results),
            selectinload(Project.publications)
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if project.script and project.script.raw_json and isinstance(project.script.raw_json, dict):
        hook_vars = project.script.raw_json.get("hook_variations")
        if hook_vars:
            setattr(project.script, "hook_variations", hook_vars)

    return project

@router.post("/{project_id}/hook")
async def select_project_hook(
    project_id: uuid.UUID,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Selects or updates the opening hook for Scene 1 of the project.
    Accepts: { "hook_key": "hook_a" | "hook_b" | "hook_c" } OR { "hook_text": "Custom hook..." }
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.script),
            selectinload(Project.scenes)
        )
        .where(Project.id == project_id)
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()

    if not project or not project.script:
        raise HTTPException(status_code=404, detail=f"Project {project_id} or script not found")

    hook_key = payload.get("hook_key")
    hook_text = payload.get("hook_text")

    if hook_key and project.script.raw_json and isinstance(project.script.raw_json, dict):
        hook_vars = project.script.raw_json.get("hook_variations", {})
        if hook_key in hook_vars:
            hook_text = hook_vars[hook_key]

    if not hook_text:
        raise HTTPException(status_code=400, detail="Invalid hook selection or missing hook_text/hook_key")

    # Update script hook
    project.script.hook = hook_text

    # Update Scene 1 narration
    if project.scenes and len(project.scenes) > 0:
        scene_1 = next((s for s in project.scenes if s.scene_number == 1), project.scenes[0])
        scene_1.narration = hook_text

    await db.commit()
    logger.info(f"[Project] Updated Project {project_id} hook to: '{hook_text[:50]}...'")

    return {
        "status": "SUCCESS",
        "selected_hook": hook_text,
        "hook_key": hook_key
    }

@router.get("/{project_id}/progress")
async def get_project_progress(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves live Redis progress percentage and current activity log for a running project,
    falling back to database project status if Redis progress is unavailable.
    """
    project_id_str = str(project_id)
    progress_data = {}

    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        if "redis:6379" in redis_url:
            try:
                socket.gethostbyname("redis")
            except Exception:
                redis_url = "redis://localhost:6379/0"

        client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=0.5, socket_connect_timeout=0.5)
        progress_data = client.hgetall(f"project_progress:{project_id_str}")
    except Exception as err:
        logger.warning(f"Could not read Redis progress for project {project_id_str}: {err}")

    # Query DB status for fallback & Watchdog check
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()

    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)

    # Watchdog Auto-fail Disabled to allow pipeline completion
    # if proj and proj.status in [ProjectStatus.RESEARCHING, ProjectStatus.SCRIPTING, ProjectStatus.GENERATING, ProjectStatus.RENDERING, ProjectStatus.QA_PENDING]:
    #     pass

    if proj and proj.status == ProjectStatus.FAILED:
        return {
            "project_id": project_id_str,
            "progress_percent": 0,
            "current_message": f"Pipeline failed: {proj.error_message or 'Asset synthesis timed out. Please retry.'}",
            "status": "FAILED",
            "stage": "Failed",
            "error": proj.error_message or "Asset synthesis timed out after 90s. Please retry.",
            "updated_at": str(now.timestamp())
        }

    if proj and proj.status == ProjectStatus.READY_FOR_REVIEW:
        return {
            "project_id": project_id_str,
            "progress_percent": 100,
            "current_message": "Pipeline completed. Ready for review.",
            "status": "COMPLETED",
            "stage": "QA Check",
            "error": None,
            "updated_at": None
        }

    if not progress_data:
        stage_map = {
            ProjectStatus.DRAFT: (5, "Research", "Starting research agent..."),
            ProjectStatus.RESEARCHING: (20, "Research", "Conducting AI topic research & trend discovery..."),
            ProjectStatus.SCRIPTING: (40, "Scripting", "Writing script & directing storyboard scenes..."),
            ProjectStatus.GENERATING: (65, "Asset Gen", "Synthesizing voiceover audio & visual frames..."),
            ProjectStatus.RENDERING: (85, "Rendering", "Rendering 1080x1920 vertical video..."),
            ProjectStatus.QA_PENDING: (95, "QA Check", "Running technical ffprobe checks & LLM QA...")
        }
        fallback_tuple = stage_map.get(proj.status, (5, "Research", "Starting research agent...")) if proj else (5, "Research", "Starting research agent...")
        return {
            "project_id": project_id_str,
            "progress_percent": fallback_tuple[0],
            "current_message": fallback_tuple[2],
            "status": "PROCESSING",
            "stage": fallback_tuple[1],
            "error": None,
            "updated_at": None
        }

    return {
        "project_id": project_id_str,
        "progress_percent": int(progress_data.get("progress_percent", 0)),
        "current_message": progress_data.get("current_message", "Processing..."),
        "status": progress_data.get("status", "PROCESSING"),
        "stage": progress_data.get("stage", ""),
        "error": progress_data.get("error", None),
        "updated_at": progress_data.get("updated_at")
    }

@router.post("/{project_id}/retry")
async def retry_project_pipeline(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Resets project status from FAILED back to GENERATING and re-triggers background asset synthesis & video rendering.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    import datetime
    project.status = ProjectStatus.GENERATING
    project.error_message = None
    project.last_heartbeat = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()

    project_id_str = str(project_id)
    logger.info(f"[Retry] Re-launching pipeline orchestrator for failed Project {project_id_str}...")

    background_tasks.add_task(run_pipeline, project_id_str)

    return {
        "status": "SUCCESS",
        "message": "Pipeline synthesis re-launched successfully.",
        "project_id": project_id_str
    }

@router.post("/{project_id}/scenes/{scene_id}/regenerate")
async def regenerate_scene(
    project_id: uuid.UUID,
    scene_id: uuid.UUID,
    payload: Dict[str, Optional[str]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers targeted single-scene asset regeneration and re-renders composite vertical video.
    Supported target_scope values: 'visual_only', 'motion_only', 'narration_only', 'full_scene'.
    """
    new_prompt = payload.get("new_prompt") if payload else None
    new_narration = payload.get("new_narration") if payload else None
    target_scope = payload.get("target_scope", "full_scene") if payload else "full_scene"

    regen_service = SceneRegenerationService()
    try:
        result = await regen_service.regenerate_single_scene(
            project_id=project_id,
            scene_id=scene_id,
            new_prompt=new_prompt,
            new_narration=new_narration,
            target_scope=target_scope,
            db_session=db
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {exc}")

@router.post("/{project_id}/approve", response_model=ContentRequestResponse)
async def approve_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Approves a project for final publishing to Qoneqt platform.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    project.status = ProjectStatus.APPROVED
    await db.commit()
    await db.refresh(project)

    logger.info(f"Project {project_id} status updated to APPROVED.")
    return project

@router.post("/{project_id}/export")
async def export_project_formats(
    project_id: uuid.UUID,
    format_profile: str = Query(default="all", alias="format"),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports rendered video into multi-format profiles:
    - 9:16 Vertical (1080x1920) - Default Reels/Shorts/TikTok
    - 16:9 Horizontal (1920x1080) - YouTube/Desktop (Auto-centered with blurred background fill)
    - 1:1 Square (1080x1080) - LinkedIn/Instagram Feed (Auto-centered with blurred background fill)
    - all - Generates all 3 profiles concurrently
    """
    from video_engine.multi_format_exporter import MultiFormatExporter, EXPORT_PROFILES

    stmt = select(Project).options(selectinload(Project.videos)).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if not project.videos or len(project.videos) == 0:
        # Check storage disk directly
        storage_dir = f"./storage/temp/{project_id}"
        default_video = os.path.join(storage_dir, f"video_{project_id}.mp4")
        if not os.path.exists(default_video):
            raise HTTPException(status_code=400, detail="No rendered video found for this project to export.")
        source_video_path = default_video
    else:
        source_video_path = project.videos[-1].file_path

    if not os.path.exists(source_video_path):
        raise HTTPException(status_code=404, detail=f"Source video file not found on disk: {source_video_path}")

    out_dir = Path(source_video_path).parent / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    exporter = MultiFormatExporter()

    try:
        if format_profile.lower() == "all":
            exports = exporter.export_all_formats(
                input_video_path=source_video_path,
                output_dir=str(out_dir),
                base_name=f"video_{project_id}"
            )
            return {
                "project_id": str(project_id),
                "status": "SUCCESS",
                "exports": {
                    fmt: {
                        "format": fmt,
                        "file_path": path,
                        "public_url": f"/storage/temp/{project_id}/exports/{os.path.basename(path)}",
                        "resolution": f"{EXPORT_PROFILES[fmt]['width']}x{EXPORT_PROFILES[fmt]['height']}"
                    }
                    for fmt, path in exports.items()
                }
            }
        else:
            fmt = format_profile.strip()
            if fmt not in EXPORT_PROFILES:
                raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Supported: {list(EXPORT_PROFILES.keys())} or 'all'")

            slug = fmt.replace(":", "_")
            out_file = str(out_dir / f"video_{project_id}_{slug}.mp4")
            exported_path = exporter.convert_format(source_video_path, out_file, target_format=fmt)

            return {
                "project_id": str(project_id),
                "status": "SUCCESS",
                "export": {
                    "format": fmt,
                    "file_path": exported_path,
                    "public_url": f"/storage/temp/{project_id}/exports/{os.path.basename(exported_path)}",
                    "resolution": f"{EXPORT_PROFILES[fmt]['width']}x{EXPORT_PROFILES[fmt]['height']}"
                }
            }
    except Exception as exc:
        logger.error(f"[MultiFormatExporter] Export failed for Project {project_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

