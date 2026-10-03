import os
import uuid
import logging
from typing import Optional, Dict, Any, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.models import (
    Project, Scene, Asset, Video, ProjectStatus, AssetType, SceneStatus
)
from backend.app.services.tts_service import BaseTTSService, EdgeTTSService, MockTTSService, get_tts_provider
from backend.app.services.visual_service import BaseVisualService, APIVisualService, MockVisualService
from backend.app.services.qa_service import QAService
from video_engine.providers import BaseVideoProvider, get_video_provider
from video_engine.subtitles import create_ass_subtitles
from video_engine.renderer import VideoRenderer

logger = logging.getLogger(__name__)

class SceneRegenerationService:
    """
    Granular single-scene regeneration engine. Supports targeted scope options:
    - 'visual_only': Regenerates keyframe image asset only.
    - 'motion_only': Regenerates Image-to-Video (I2V) motion clip only.
    - 'narration_only': Regenerates TTS voiceover audio only.
    - 'full_scene': Regenerates keyframe image, motion clip, and narration audio.

    Re-composites final vertical video reusing cached assets for all other unchanged scenes and re-executes QA.
    """
    def __init__(
        self,
        tts_service: Optional[BaseTTSService] = None,
        visual_service: Optional[BaseVisualService] = None,
        video_provider: Optional[BaseVideoProvider] = None,
        renderer: Optional[VideoRenderer] = None,
        qa_service: Optional[QAService] = None,
        storage_dir: str = "./storage/temp"
    ):
        self.tts_service = tts_service or get_tts_provider()
        self.visual_service = visual_service or (MockVisualService() if use_mock else APIVisualService())
        self.video_provider = video_provider or get_video_provider()
        self.renderer = renderer or VideoRenderer(video_provider=self.video_provider, temp_dir=storage_dir)
        self.qa_service = qa_service or QAService()
        self.storage_dir = storage_dir

    async def regenerate_single_scene(
        self,
        project_id: Union[str, uuid.UUID],
        scene_id: Union[str, uuid.UUID],
        new_prompt: Optional[str] = None,
        new_narration: Optional[str] = None,
        target_scope: str = "full_scene",
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Regenerates assets for a targeted single scene based on specified target_scope,
        while reusing cached assets for all other scenes.
        """
        proj_uuid = uuid.UUID(str(project_id))
        scene_uuid = uuid.UUID(str(scene_id))
        scope = (target_scope or "full_scene").lower()

        logger.info(f"[SceneRegenerationService] Targeted Scene={scene_uuid} (Scope='{scope}') for Project={proj_uuid}")

        scene_dir = os.path.join(self.storage_dir, str(proj_uuid))
        work_dir = os.path.join(scene_dir, "render_work")
        os.makedirs(scene_dir, exist_ok=True)
        os.makedirs(work_dir, exist_ok=True)

        target_scene: Optional[Scene] = None
        all_scenes: list[Scene] = []

        if db_session:
            stmt = select(Project).options(
                selectinload(Project.scenes),
                selectinload(Project.script)
            ).where(Project.id == proj_uuid)
            
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()

            if project:
                all_scenes = sorted(project.scenes, key=lambda s: s.scene_number)
                target_scene = next((s for s in all_scenes if s.id == scene_uuid), None)

        if not target_scene:
            raise ValueError(f"Scene {scene_uuid} not found for Project {proj_uuid}")

        # Update prompts if provided
        if new_prompt:
            target_scene.visual_prompt = new_prompt

        if new_narration:
            target_scene.narration = new_narration

        target_scene.status = SceneStatus.GENERATING

        img_path = os.path.join(scene_dir, f"image_scene_{target_scene.scene_number}.png")
        clip_path = os.path.join(work_dir, f"clip_{target_scene.scene_number - 1:03d}.mp4")
        audio_path = os.path.join(scene_dir, f"audio_scene_{target_scene.scene_number}.mp3")

        # 1. Targeted Asset Regeneration based on scope
        if scope in ("visual_only", "full_scene"):
            await self.visual_service.generate_visual(
                prompt=target_scene.visual_prompt,
                output_path=img_path,
                aspect_ratio="9:16"
            )

        if scope in ("motion_only", "visual_only", "full_scene"):
            motion_prompt = target_scene.motion_prompt or target_scene.camera_direction or "Slow push-in zoom"
            await self.video_provider.generate_motion_clip(
                image_path=img_path,
                motion_prompt=motion_prompt,
                duration=target_scene.duration,
                output_path=clip_path,
                aspect_ratio="9:16"
            )

        if scope in ("narration_only", "full_scene") or new_narration or not os.path.exists(audio_path):
            if hasattr(self.tts_service, "generate_speech_with_metadata"):
                tts_info = await self.tts_service.generate_speech_with_metadata(
                    text=target_scene.narration,
                    output_path=audio_path
                )
                tts_dur = tts_info.get("duration", 3.0)
            else:
                tts_dur = await self.tts_service.generate_speech(
                    text=target_scene.narration,
                    output_path=audio_path
                )
            target_scene.duration = max(2.5, round(tts_dur + 0.4, 2))

        target_scene.status = SceneStatus.COMPLETED

        # 2. Gather cached assets for all project scenes
        scene_assets_list = []
        audio_paths_list = []
        subtitle_data = []

        for sc in all_scenes:
            sc_img = os.path.join(scene_dir, f"image_scene_{sc.scene_number}.png")
            sc_clip = os.path.join(work_dir, f"clip_{sc.scene_number - 1:03d}.mp4")
            sc_aud = os.path.join(scene_dir, f"audio_scene_{sc.scene_number}.mp3")

            scene_assets_list.append({
                "image_path": sc_img,
                "motion_clip_path": sc_clip if os.path.exists(sc_clip) else None,
                "duration": sc.duration,
                "motion_prompt": sc.motion_prompt or sc.camera_direction,
                "kinetic_text": sc.kinetic_text
            })
            audio_paths_list.append(sc_aud)
            subtitle_data.append({
                "narration": sc.narration,
                "caption": sc.caption,
                "duration": sc.duration,
                "kinetic_text": sc.kinetic_text
            })

        # 3. Generate updated .ass dual-layer subtitles
        subtitle_ass_path = os.path.join(scene_dir, "subtitles.ass")
        create_ass_subtitles(subtitle_data, subtitle_ass_path)

        # 4. Re-render vertical video reusing cached scene assets
        out_video_path = os.path.join(scene_dir, f"video_{proj_uuid}.mp4")
        rendered_video = self.renderer.render_vertical_video(
            scene_assets=scene_assets_list,
            audio_paths=audio_paths_list,
            subtitle_ass_path=subtitle_ass_path,
            output_video_path=out_video_path
        )

        # 5. Evaluate QA on new composite video
        script_dict = {
            "title": project.script.title if project and project.script else "Video",
            "hook": project.script.hook if project and project.script else "",
            "scenes": subtitle_data
        }
        
        target_dur = project.duration if project else 30
        qa_res = await self.qa_service.evaluate_video(
            project_id=proj_uuid,
            video_path=rendered_video,
            script_data=script_dict,
            target_duration=target_dur,
            db_session=db_session
        )

        # 6. Update Project status back to READY_FOR_REVIEW
        if db_session and project:
            project.status = ProjectStatus.READY_FOR_REVIEW
            await db_session.commit()

        logger.info(f"[SceneRegenerationService] Granular scene regeneration complete. Video at {rendered_video}")

        return {
            "project_id": str(proj_uuid),
            "scene_id": str(scene_uuid),
            "target_scope": scope,
            "regenerated_visual_path": img_path,
            "regenerated_audio_path": audio_path,
            "output_video_path": rendered_video,
            "qa_status": qa_res.final_status.value if hasattr(qa_res.final_status, "value") else str(qa_res.final_status),
            "project_status": ProjectStatus.READY_FOR_REVIEW.value
        }
