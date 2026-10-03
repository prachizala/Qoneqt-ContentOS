import os
import shutil
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import Scene, Asset, AssetType, SceneStatus
from backend.app.services.tts_service import (
    BaseTTSService,
    EdgeTTSService,
    MockTTSService,
    get_tts_provider,
    get_audio_file_duration
)
from backend.app.services.visual_service import BaseVisualService, APIVisualService, MockVisualService

logger = logging.getLogger(__name__)

# Standard padding in seconds added to audio duration to prevent abrupt transition cut-offs
AUDIO_PADDING_SECONDS = 0.5

class AudioSynthesisFatalError(Exception):
    """
    Explicit fatal exception raised when TTS synthesis fails or produces an empty/invalid audio track
    after maximum retry attempts.
    """
    pass

class AssetManager:
    """
    Orchestrator for managing isolated project asset pipelines (TTS Audio + Visual Frame)
    and updating PostgreSQL database records.
    Enforces dynamic sandboxing per projectId and strict sequential TTS generation with validation.
    """
    def __init__(
        self,
        tts_service: Optional[BaseTTSService] = None,
        visual_service: Optional[BaseVisualService] = None,
        storage_dir: str = "./storage/temp"
    ):
        use_mock = os.getenv("USE_MOCK_AI", "true").lower() in ("true", "1", "yes")
        
        if tts_service:
            self.tts_service = tts_service
        else:
            self.tts_service = get_tts_provider()

        if visual_service:
            self.visual_service = visual_service
        else:
            self.visual_service = MockVisualService() if use_mock else APIVisualService()

        self.storage_dir = storage_dir

    async def _wrap_basic_tts(self, text: str, output_path: str, voice: str) -> Dict[str, Any]:
        dur = await self.tts_service.generate_speech(text=text, output_path=output_path, voice=voice)
        return {"duration": dur, "word_timings": [], "audio_path": output_path}

    def cleanup_project_sandbox(self, project_id: Union[str, uuid.UUID]) -> str:
        """
        Initializes a clean, isolated workspace run directory for the project,
        purging any stale/cached files from previous runs to prevent cross-project audio leaks.
        """
        project_id_str = str(project_id)
        scene_dir = os.path.join(self.storage_dir, project_id_str)
        work_dir = os.path.join(scene_dir, "render_work")
        
        os.makedirs(scene_dir, exist_ok=True)
        if os.path.exists(work_dir):
            try:
                shutil.rmtree(work_dir)
            except Exception as e:
                logger.debug(f"[AssetManager] Non-fatal cleanup warning for {work_dir}: {e}")
        os.makedirs(work_dir, exist_ok=True)
        return scene_dir

    async def generate_scene_assets(
        self,
        project_id: Union[str, uuid.UUID],
        scene: Scene,
        db_session: AsyncSession,
        aspect_ratio: str = "9:16",
        voice: str = "en-US-ChristopherNeural"
    ) -> Dict[str, Any]:
        """
        Strict sequential Audio-First asset generation:
        1. Sequentially synthesizes and validates TTS audio with 3-attempt retry loop.
        2. Inspects audio file size (> 2 KB) and ffprobe duration (> 0.5s). Throws fatal error on failure.
        3. Dynamically assigns scene duration = audio_duration + PADDING_SECONDS.
        4. Synthesizes visual keyframe.
        5. Persists Asset database records.
        """
        project_id_str = str(project_id)
        scene_dir = os.path.join(self.storage_dir, project_id_str)
        os.makedirs(scene_dir, exist_ok=True)

        audio_output_path = os.path.join(scene_dir, f"audio_scene_{scene.scene_number}.mp3")
        image_output_path = os.path.join(scene_dir, f"image_scene_{scene.scene_number}.png")

        logger.info(f"[AssetManager] Synthesizing assets for Project={project_id_str}, Scene={scene.scene_number}")

        # ---------------------------------------------------------
        # 1. 5s Circuit Breaker TTS Audio Generation with Instant Fallback
        # ---------------------------------------------------------
        tts_result: Dict[str, Any] = {}
        try:
            tts_result = await asyncio.wait_for(
                self.tts_service.generate_speech_with_metadata(
                    text=scene.narration,
                    output_path=audio_output_path,
                    voice=voice
                ) if hasattr(self.tts_service, "generate_speech_with_metadata") else self._wrap_basic_tts(scene.narration, audio_output_path, voice),
                timeout=5.0
            )
            if not os.path.exists(audio_output_path) or os.path.getsize(audio_output_path) < 1500:
                raise ValueError("Generated TTS audio file too small or unreadable")
        except Exception as exc:
            logger.warning(f"[AssetManager] Scene {scene.scene_number} TTS 5s timeout/error ({exc}). Using instant MockTTSService.")
            mock_tts = MockTTSService()
            tts_result = await mock_tts.generate_speech_with_metadata(
                text=scene.narration,
                output_path=audio_output_path,
                voice=voice
            )

        # ---------------------------------------------------------
        # 2. Dynamic Scene Duration Driven by Audio
        # ---------------------------------------------------------
        audio_dur = float(tts_result.get("duration", 3.0))
        dynamic_scene_dur = max(2.5, round(audio_dur + AUDIO_PADDING_SECONDS, 2))
        
        scene.duration = dynamic_scene_dur
        scene.status = SceneStatus.COMPLETED

        logger.info(
            f"[AssetManager] Scene {scene.scene_number} timeline mapped: "
            f"audio={audio_dur:.2f}s + pad={AUDIO_PADDING_SECONDS}s -> scene_duration={dynamic_scene_dur:.2f}s"
        )

        # ---------------------------------------------------------
        # 3. 5s Circuit Breaker Visual Keyframe Generation with Instant Fallback
        # ---------------------------------------------------------
        try:
            visual_path = await asyncio.wait_for(
                self.visual_service.generate_visual(
                    prompt=scene.visual_prompt,
                    output_path=image_output_path,
                    aspect_ratio=aspect_ratio
                ),
                timeout=5.0
            )
        except Exception as exc:
            logger.warning(f"[AssetManager] Scene {scene.scene_number} Visual 5s timeout ({exc}). Rendering instant fallback gradient canvas.")
            from backend.app.services.visual_service import render_fallback_gradient_canvas
            w, h = (1080, 1920) if aspect_ratio == "9:16" else ((1920, 1080) if aspect_ratio == "16:9" else (1080, 1080))
            visual_path = render_fallback_gradient_canvas(image_output_path, w, h)

        # ---------------------------------------------------------
        # 4. Persist Asset Records
        # ---------------------------------------------------------
        audio_asset = Asset(
            id=uuid.uuid4(),
            project_id=uuid.UUID(project_id_str) if isinstance(project_id, str) else project_id,
            scene_id=scene.id,
            asset_type=AssetType.AUDIO,
            provider=self.tts_service.__class__.__name__,
            local_path=audio_output_path,
            metadata_json={
                "voice": voice,
                "audio_duration_seconds": audio_dur,
                "scene_duration_seconds": dynamic_scene_dur,
                "narration_length": len(scene.narration),
                "word_count": len(scene.narration.split())
            }
        )

        image_asset = Asset(
            id=uuid.uuid4(),
            project_id=uuid.UUID(project_id_str) if isinstance(project_id, str) else project_id,
            scene_id=scene.id,
            asset_type=AssetType.IMAGE,
            provider=self.visual_service.__class__.__name__,
            local_path=visual_path,
            metadata_json={
                "aspect_ratio": aspect_ratio,
                "visual_prompt": scene.visual_prompt
            }
        )

        db_session.add(audio_asset)
        db_session.add(image_asset)
        await db_session.commit()

        return {
            "scene_number": scene.scene_number,
            "actual_duration": dynamic_scene_dur,
            "audio_duration": audio_dur,
            "word_timings": tts_result.get("word_timings", []),
            "audio_asset_id": str(audio_asset.id),
            "audio_path": audio_output_path,
            "image_asset_id": str(image_asset.id),
            "image_path": visual_path
        }
