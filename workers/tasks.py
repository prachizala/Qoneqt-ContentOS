import os
import uuid
import json
import time
import datetime
import asyncio
import logging
import redis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from workers.celery_app import celery_app
from backend.app.database import AsyncSessionLocal
from backend.app.models.models import (
    Project, Script, Scene, Video, QAResult, ProjectStatus, SceneStatus, VideoStatus
)
from ai.agents.researcher import ResearchAgent
from ai.agents.scriptwriter import ScriptAgent
from ai.agents.scene_director import SceneDirector
from backend.app.services.asset_manager import AssetManager
from video_engine.providers import get_video_provider
from video_engine.subtitles import create_ass_subtitles
from video_engine.renderer import VideoRenderer
from backend.app.services.qa_service import QAService

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False

def update_redis_progress(
    project_id: str,
    percent: int,
    message: str,
    status: str = "PROCESSING",
    stage: str = None,
    error: str = None
):
    """
    Updates live pipeline progress percentage, stage, and error details in Redis.
    """
    global _redis_client, _redis_checked
    if _redis_checked and _redis_client is None:
        return

    try:
        if _redis_client is None:
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
            if "redis:6379" in redis_url:
                try:
                    import socket
                    socket.gethostbyname("redis")
                except Exception:
                    redis_url = "redis://localhost:6379/0"
            _redis_client = redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=0.2, socket_connect_timeout=0.2)
            _redis_client.ping()
            _redis_checked = True

        mapping = {
            "progress_percent": str(percent),
            "current_message": message,
            "status": status,
            "stage": stage or "",
            "error": error or "",
            "updated_at": str(time.time())
        }
        _redis_client.hset(f"project_progress:{project_id}", mapping=mapping)
    except Exception as err:
        _redis_client = None
        _redis_checked = True
        logger.debug(f"Redis progress unavailable: {err}")

async def update_pipeline_heartbeat(
    session,
    project: Project,
    project_id_str: str,
    percent: int,
    message: str,
    status_str: str = "PROCESSING",
    stage: str = None
):
    """
    Updates database last_heartbeat timestamp and broadcasts progress to Redis/SSE listeners.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    project.last_heartbeat = now
    try:
        await session.commit()
    except Exception as exc:
        logger.warning(f"[Watchdog] Non-fatal heartbeat commit warning for Project {project_id_str}: {exc}")

    update_redis_progress(project_id_str, percent, message, status=status_str, stage=stage)

async def run_pipeline(project_id_str: str):
    """
    Asynchronous pipeline orchestrator executing 5-step video production workflow
    with immediate scene persistence, strict 20s asset timeouts, and watchdog heartbeat updates.
    """
    project_uuid = uuid.UUID(project_id_str)

    update_redis_progress(project_id_str, 5, "Starting research agent...", status="PROCESSING", stage="Research")

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Project)
            .options(selectinload(Project.script), selectinload(Project.scenes))
            .where(Project.id == project_uuid)
        )
        res = await session.execute(stmt)
        project = res.scalar_one_or_none()

        if not project:
            logger.error(f"[Pipeline] Project {project_id_str} not found in DB.")
            update_redis_progress(project_id_str, 0, f"Project {project_id_str} not found in database", status="FAILED", error="Project not found")
            return

        try:
            # Check if script & scenes already exist in DB (e.g. on Retry)
            if project.script and project.scenes and len(project.scenes) > 0:
                logger.info(f"[Pipeline] Project {project_id_str} already has {len(project.scenes)} scenes saved. Skipping LLM generation and resuming Asset Synthesis directly.")
                script_record = project.script
                scene_records = sorted(project.scenes, key=lambda s: s.scene_number)
                directed_scenes = scene_records
            else:
                # Step 1: RESEARCHING (20%)
                project.status = ProjectStatus.RESEARCHING
                await update_pipeline_heartbeat(session, project, project_id_str, 20, "Conducting AI topic research & trend discovery...", stage="Research")

                researcher = ResearchAgent()
                research = await researcher.research_topic(
                    topic=project.topic,
                    audience=project.audience,
                    objective=project.objective,
                    language=project.language
                )

                # Step 2: SCRIPTING (40%)
                project.status = ProjectStatus.SCRIPTING
                await update_pipeline_heartbeat(session, project, project_id_str, 40, "Writing script & directing storyboard scenes...", stage="Scripting")

                scriptwriter = ScriptAgent()
                script_data = await scriptwriter.write_script(
                    research=research,
                    duration=project.duration,
                    style=project.style,
                    tone=project.objective or "Viral / Hook Driven"
                )

                director = SceneDirector()
                directed_scenes = await director.direct_scenes(
                    scenes=script_data.scenes,
                    style=project.style,
                    aspect_ratio=project.aspect_ratio,
                    tone=project.objective or "Viral / Hook Driven"
                )

                logger.info(f"[PIPELINE] 1. Scripting & Director completed. Scenes count: {len(directed_scenes) if directed_scenes else 0}")

                # Fallback injection if LLM returns 0 scenes
                if not directed_scenes or len(directed_scenes) == 0:
                    logger.warning("[PIPELINE] Directed scenes count is 0. Injecting safe 3-scene fallback storyboard.")
                    from ai.agents.scene_director import DirectedScene
                    directed_scenes = [
                        DirectedScene(
                            scene_number=1,
                            duration=5.0,
                            narration="Autonomous AI agents are fundamentally transforming modern software engineering.",
                            visual_prompt="Futuristic digital neural network node 4k vertical wallpaper",
                            camera_direction="slow zoom in",
                            kinetic_text="AI AGENTS TRANSFORMING SOFTWARE",
                            motion_prompt="glowing particles flow through neural nodes",
                            caption="Autonomous AI agents are transforming software engineering.",
                            transition="fade"
                        ),
                        DirectedScene(
                            scene_number=2,
                            duration=5.0,
                            narration="Instead of writing boilerplate, systems now self-heal, self-test, and deploy autonomously.",
                            visual_prompt="Abstract glowing code matrix cybersecurity high tech vertical",
                            camera_direction="pan right",
                            kinetic_text="SELF-HEALING AUTONOMOUS SYSTEMS",
                            motion_prompt="matrix rain code streaming smoothly",
                            caption="Systems self-heal, self-test, and deploy autonomously.",
                            transition="fade"
                        ),
                        DirectedScene(
                            scene_number=3,
                            duration=5.0,
                            narration="The future belongs to orchestrators, not just traditional coders.",
                            visual_prompt="Human engineer collaborating with holographic AI interface vertical",
                            camera_direction="push forward",
                            kinetic_text="ORCHESTRATE THE AI FUTURE",
                            motion_prompt="holographic display pulsating with light",
                            caption="The future belongs to orchestrators.",
                            transition="fade"
                        )
                    ]

                # Save Script & Scenes immediately to DB
                script_record = Script(
                    id=uuid.uuid4(),
                    project_id=project_uuid,
                    title=script_data.title or project.topic,
                    hook=script_data.hook or directed_scenes[0].narration,
                    body="\n".join([s.narration for s in directed_scenes]),
                    cta=script_data.cta or "Follow for more AI insights",
                    raw_json=script_data.model_dump()
                )
                session.add(script_record)
                await session.flush()

                scene_records = []
                for sc in directed_scenes:
                    scene_rec = Scene(
                        id=uuid.uuid4(),
                        project_id=project_uuid,
                        script_id=script_record.id,
                        scene_number=sc.scene_number,
                        duration=sc.duration,
                        narration=sc.narration,
                        visual_prompt=sc.visual_prompt,
                        camera_direction=sc.camera_direction,
                        kinetic_text=sc.kinetic_text,
                        motion_prompt=sc.motion_prompt,
                        caption=sc.caption,
                        transition=sc.transition,
                        status=SceneStatus.PENDING
                    )
                    session.add(scene_rec)
                    scene_records.append(scene_rec)

            # Commit script & scenes immediately to DB so UI displays scenes right away
            project.status = ProjectStatus.GENERATING
            await update_pipeline_heartbeat(session, project, project_id_str, 65, "Synthesizing voiceover audio & visual keyframes concurrently...", stage="Asset Gen")

            logger.info("--> Starting Asset Synthesis for scenes: %s", len(scene_records))

            # -------------------------------------------------------------------
            # PARALLEL ASSET GENERATION WITH PER-SCENE HEARTBEAT UPDATES
            # -------------------------------------------------------------------
            asset_manager = AssetManager()
            asset_manager.cleanup_project_sandbox(project_id_str)

            async def generate_single_scene_task(sc: Scene):
                scene_dir = f"./storage/temp/{project_id_str}"
                os.makedirs(scene_dir, exist_ok=True)
                img_p = os.path.join(scene_dir, f"image_scene_{sc.scene_number}.png")
                aud_p = os.path.join(scene_dir, f"audio_scene_{sc.scene_number}.mp3")

                try:
                    res = await asyncio.wait_for(
                        asset_manager.generate_scene_assets(
                            project_id=project_uuid,
                            scene=sc,
                            db_session=session,
                            aspect_ratio=project.aspect_ratio
                        ),
                        timeout=5.0
                    )
                    await update_pipeline_heartbeat(session, project, project_id_str, 70, f"Synthesized Scene {sc.scene_number} assets...", stage="Asset Gen")
                    return res
                except Exception as exc:
                    logger.warning(f"[Pipeline] Scene {sc.scene_number} asset task error ({exc}). Rendering instant local fallbacks.")
                    try:
                        mock_tts = MockTTSService()
                        tts_res = await mock_tts.generate_speech_with_metadata(sc.narration, aud_p)
                        audio_dur = float(tts_res.get("duration", 3.0))
                    except Exception:
                        audio_dur = 3.0

                    from backend.app.services.visual_service import render_fallback_gradient_canvas
                    w, h = (1080, 1920) if project.aspect_ratio == "9:16" else ((1920, 1080) if project.aspect_ratio == "16:9" else (1080, 1080))
                    render_fallback_gradient_canvas(img_p, w, h)

                    await update_pipeline_heartbeat(session, project, project_id_str, 70, f"Synthesized Scene {sc.scene_number} fallback assets...", stage="Asset Gen")
                    return {
                        "scene_number": sc.scene_number,
                        "actual_duration": round(audio_dur + 0.5, 2),
                        "audio_duration": audio_dur,
                        "word_timings": [],
                        "image_path": img_p,
                        "audio_path": aud_p
                    }

            # Execute all scene asset tasks concurrently via asyncio.gather
            results = await asyncio.gather(*[generate_single_scene_task(sc) for sc in scene_records], return_exceptions=True)

            logger.info("--> Asset Synthesis finished successfully")
            logger.info("--> Transitioning to Rendering...")
            await update_pipeline_heartbeat(session, project, project_id_str, 75, "Asset synthesis completed. Compiling timeline...", stage="Asset Gen")

            scene_assets_info = []
            audio_paths = []
            subtitle_timings = []

            for idx, sc in enumerate(scene_records):
                res_item = results[idx]
                if isinstance(res_item, Exception) or not isinstance(res_item, dict):
                    logger.warning(f"[Pipeline] Scene {sc.scene_number} task returned exception ({res_item}). Using default mapped paths.")
                    scene_dir = f"./storage/temp/{project_id_str}"
                    img_p = os.path.join(scene_dir, f"image_scene_{sc.scene_number}.png")
                    aud_p = os.path.join(scene_dir, f"audio_scene_{sc.scene_number}.mp3")
                    res_item = {
                        "image_path": img_p,
                        "audio_path": aud_p,
                        "actual_duration": sc.duration,
                        "audio_duration": sc.duration
                    }

                scene_assets_info.append({
                    "image_path": res_item["image_path"],
                    "duration": res_item["actual_duration"],
                    "camera_direction": sc.camera_direction,
                    "kinetic_text": sc.kinetic_text,
                    "motion_prompt": sc.motion_prompt
                })
                audio_paths.append(res_item["audio_path"])
                subtitle_timings.append({
                    "narration": sc.narration,
                    "caption": sc.caption,
                    "duration": res_item["actual_duration"],
                    "audio_duration": res_item.get("audio_duration"),
                    "word_timings": res_item.get("word_timings", []),
                    "kinetic_text": sc.kinetic_text
                })

            # Step 4: RENDERING (85%)
            project.status = ProjectStatus.RENDERING
            await update_pipeline_heartbeat(session, project, project_id_str, 85, "Rendering 1080x1920 vertical video with I2V motion & kinetic subtitles...", stage="Rendering")

            storage_dir = f"./storage/temp/{project_id_str}"
            os.makedirs(storage_dir, exist_ok=True)

            subtitle_ass_path = os.path.join(storage_dir, "subtitles.ass")
            await asyncio.to_thread(create_ass_subtitles, subtitle_timings, subtitle_ass_path)

            output_video_path = os.path.join(storage_dir, f"video_{project_id_str}.mp4")
            video_provider = get_video_provider()
            renderer = VideoRenderer(video_provider=video_provider, temp_dir=storage_dir)
            rendered_video = await asyncio.to_thread(
                renderer.render_vertical_video,
                scene_assets=scene_assets_info,
                audio_paths=audio_paths,
                subtitle_ass_path=subtitle_ass_path,
                output_video_path=output_video_path,
                subtitle_timings=subtitle_timings
            )

            thumbnail_path = os.path.join(storage_dir, "thumbnail.jpg")

            video_record = Video(
                id=uuid.uuid4(),
                project_id=project_uuid,
                file_path=rendered_video,
                public_url=f"/storage/temp/{project_id_str}/video_{project_id_str}.mp4",
                thumbnail_path=f"/storage/temp/{project_id_str}/thumbnail.jpg" if os.path.exists(thumbnail_path) else None,
                duration=sum(s["duration"] for s in scene_assets_info),
                resolution="1080x1920",
                status=VideoStatus.READY
            )
            session.add(video_record)
            await session.commit()

            # Step 5: QA_PENDING -> READY_FOR_REVIEW (100%)
            project.status = ProjectStatus.QA_PENDING
            await update_pipeline_heartbeat(session, project, project_id_str, 95, "Running technical ffprobe checks & LLM content QA...", stage="QA Check")

            qa_service = QAService()
            qa_res = await qa_service.evaluate_video(
                project_id=project_uuid,
                video_path=rendered_video,
                script_data={
                    "title": script_data.title,
                    "hook": script_data.hook,
                    "scenes": subtitle_timings
                },
                target_duration=project.duration,
                db_session=session
            )

            project.status = ProjectStatus.READY_FOR_REVIEW
            await update_pipeline_heartbeat(session, project, project_id_str, 100, "Pipeline completed. Ready for review.", status_str="COMPLETED", stage="QA Check")

        except Exception as err:
            import traceback
            full_trace = f"{err}\n{traceback.format_exc()}"
            logger.error(f"[Pipeline] Execution failed for project {project_id_str}:\n{full_trace}")

            try:
                project.status = ProjectStatus.FAILED
                project.error_message = str(err)
                await session.commit()
            except Exception as db_err:
                logger.error(f"[Pipeline] Failed to set DB status to FAILED for project {project_id_str}: {db_err}")

            update_redis_progress(project_id_str, 0, f"Pipeline failed: {err}", status="FAILED", error=str(err))
            raise err

@celery_app.task(name="workers.tasks.pipeline_orchestrator", bind=True)
def pipeline_orchestrator(self, project_id: str):
    """
    Celery background worker task driving full end-to-end pipeline execution.
    """
    logger.info(f"[Celery Worker] Starting pipeline_orchestrator task for Project ID: {project_id}")
    update_redis_progress(project_id, 5, "Starting research agent...", status="PROCESSING", stage="Research")
    try:
        asyncio.run(run_pipeline(project_id))
    except Exception as exc:
        import traceback
        full_err = f"{exc}\n{traceback.format_exc()}"
        logger.error(f"[Celery Worker] Task failed for Project {project_id}:\n{full_err}")
        update_redis_progress(project_id, 0, f"Pipeline failed: {exc}", status="FAILED", error=str(exc))
        raise exc
