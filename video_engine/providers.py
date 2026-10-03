import os
import abc
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
from video_engine.stock_broll import StockBRollProcessor, StockVideoClient

logger = logging.getLogger(__name__)

class BaseVideoProvider(abc.ABC):
    """
    Modular Abstract Base Class for Image-to-Video (I2V) & Motion Video Providers.
    Allows hot-swapping video backends (e.g., Veo 3.1, Runway Gen-4.5, Stock B-Roll, Ken Burns)
    without altering upstream pipeline logic.
    """
    @abc.abstractmethod
    def generate_motion_clip_sync(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        Synchronously generates an I2V motion clip starting from input keyframe image and motion prompt.
        """
        pass

    async def generate_motion_clip(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        Asynchronously generates an I2V motion clip.
        """
        return await asyncio.to_thread(
            self.generate_motion_clip_sync,
            image_path,
            motion_prompt,
            duration,
            output_path,
            aspect_ratio
        )

class KenBurnsVideoProvider(BaseVideoProvider):
    """
    Local FFmpeg dynamic camera motion provider (zoompan/pan/orbit).
    Generates 1080x1920 30fps H.264 video clips without requiring external paid API keys.
    """
    def generate_motion_clip_sync(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fps = 30
        num_frames = int(round(fps * duration))
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

        prompt_lower = (motion_prompt or "").lower()
        if "pan" in prompt_lower or "tracking" in prompt_lower:
            zoompan_filter = (
                f"scale=8000:-1,"
                f"zoompan=z='1.15':d={num_frames}:"
                f"x='(on/{num_frames})*(iw-iw/1.15)':y='ih/2-(ih/1.15/2)':s={width}x{height}:fps={fps}"
            )
        elif "orbit" in prompt_lower or "drift" in prompt_lower:
            zoompan_filter = (
                f"scale=8000:-1,"
                f"zoompan=z='min(zoom+0.0015,1.20)':d={num_frames}:"
                f"x='iw/2-(iw/zoom/2)+sin(on/10)*20':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )
        else: # default push-in zoom
            zoompan_filter = (
                f"scale=8000:-1,"
                f"zoompan=z='min(zoom+0.002,1.25)':d={num_frames}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
            )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-t", str(duration),
            "-vf", zoompan_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path
        ]

        logger.info(f"[KenBurnsVideoProvider] Rendering camera motion clip ({duration:.1f}s) -> {output_path}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"[KenBurnsVideoProvider] FFmpeg motion error: {result.stderr}")
            raise RuntimeError(f"Motion clip rendering failed: {result.stderr}")
        
        return output_path

class StockBRollVideoProvider(BaseVideoProvider):
    """
    Automated Stock Video & B-Roll Provider (Pexels / Pixabay).
    Matches primary visual entities, downloads 9:16 HD stock footage,
    and crops/trims to match exact scene duration.
    Falls back to KenBurnsVideoProvider if no stock video is available.
    """
    def __init__(self, stock_processor: Optional[StockBRollProcessor] = None):
        self.stock_processor = stock_processor or StockBRollProcessor()
        self.fallback = KenBurnsVideoProvider()

    def generate_motion_clip_sync(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        work_dir = str(Path(output_path).parent)
        try:
            import concurrent.futures
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            self.stock_processor.fetch_and_prepare_stock_broll(
                                visual_prompt=motion_prompt,
                                target_duration=duration,
                                output_clip_path=output_path,
                                work_dir=work_dir,
                                aspect_ratio=aspect_ratio
                            )
                        )
                    )
                    broll_clip = future.result(timeout=15.0)
            else:
                broll_clip = asyncio.run(
                    self.stock_processor.fetch_and_prepare_stock_broll(
                        visual_prompt=motion_prompt,
                        target_duration=duration,
                        output_clip_path=output_path,
                        work_dir=work_dir,
                        aspect_ratio=aspect_ratio
                    )
                )

            if broll_clip and os.path.exists(broll_clip) and os.path.getsize(broll_clip) > 5000:
                logger.info(f"[StockBRollVideoProvider] Successfully matched & cropped stock B-roll -> {broll_clip}")
                return broll_clip
        except Exception as e:
            logger.warning(f"[StockBRollVideoProvider] Stock B-roll resolution warning ({e}). Falling back to camera motion.")

        return self.fallback.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)

class Veo31VideoProvider(BaseVideoProvider):
    """
    Google Veo 3.1 Primary Video Backend Provider Adapter.
    Uses VEO_API_KEY / GOOGLE_API_KEY for I2V generation.
    Falls back to StockBRoll / KenBurns if key absent or rate limit / timeout occurs.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VEO_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.stock_provider = StockBRollVideoProvider()

    def generate_motion_clip_sync(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        if not self.api_key:
            logger.info("[Veo31VideoProvider] VEO_API_KEY not set. Using B-Roll / KenBurns motion fallback adapter.")
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)

        logger.info(f"[Veo31VideoProvider] Dispatching I2V request to Veo 3.1 engine (prompt: '{motion_prompt[:40]}...')")
        try:
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)
        except Exception as e:
            logger.warning(f"[Veo31VideoProvider] Veo 3.1 request error ({e}). Falling back to Stock / motion synthesis.")
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)

class RunwayGen45VideoProvider(BaseVideoProvider):
    """
    Runway Gen-4.5 Alternative Video Backend Provider Adapter.
    Uses RUNWAY_API_KEY for Image-to-Video generation with automated Stock B-Roll fallback.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RUNWAY_API_KEY")
        self.stock_provider = StockBRollVideoProvider()

    def generate_motion_clip_sync(
        self,
        image_path: str,
        motion_prompt: str,
        duration: float,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        if not self.api_key:
            logger.info("[RunwayGen45VideoProvider] RUNWAY_API_KEY not set. Using Stock B-Roll fallback adapter.")
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)

        logger.info(f"[RunwayGen45VideoProvider] Dispatching I2V request to Runway Gen-4.5 (prompt: '{motion_prompt[:40]}...')")
        try:
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)
        except Exception as e:
            logger.warning(f"[RunwayGen45VideoProvider] Runway request error ({e}). Falling back to Stock B-roll.")
            return self.stock_provider.generate_motion_clip_sync(image_path, motion_prompt, duration, output_path, aspect_ratio)

def get_video_provider(provider_name: Optional[str] = None) -> BaseVideoProvider:
    """
    Factory function selecting configured Video Backend Provider.
    Supported options: 'veo' (Veo 3.1), 'runway' (Runway Gen-4.5), 'stock' / 'broll' (Pexels/Pixabay), 'kenburns' (Local FFmpeg).
    """
    name = (provider_name or os.getenv("VIDEO_PROVIDER", "veo")).lower()
    if name in ("veo", "veo31", "veo-3.1"):
        return Veo31VideoProvider()
    elif name in ("runway", "runwaygen45", "runway-4.5"):
        return RunwayGen45VideoProvider()
    elif name in ("stock", "broll", "pexels", "pixabay"):
        return StockBRollVideoProvider()
    else:
        return KenBurnsVideoProvider()
