import os
import abc
import random
import logging
import asyncio
import urllib.parse
import httpx
from pathlib import Path
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

def render_fallback_gradient_canvas(output_path: str, width: int = 1080, height: int = 1920) -> str:
    """
    Generates a clean dark aesthetic vertical gradient background canvas without any text overlays.
    Used as instantaneous < 10ms offline fallback when external visual APIs time out or fail.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color=(10, 15, 30))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(12 + ratio * 35)
        g = int(20 + ratio * 50)
        b = int(45 + ratio * 90)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    colors = [(14, 165, 233), (99, 102, 241), (236, 72, 153), (16, 185, 129)]
    for i in range(6):
        c_x = int(width * (0.2 + (i * 0.15)))
        c_y = int(height * (0.2 + ((i % 3) * 0.25)))
        radius = int(width * (0.3 + ((i % 2) * 0.15)))
        col = colors[i % len(colors)]
        draw.ellipse([c_x - radius, c_y - radius, c_x + radius, c_y + radius], outline=col, width=4)

    img.save(output_path, "PNG")
    logger.info(f"[VisualFallback] Created aesthetic gradient background canvas -> {output_path}")
    return output_path

class BaseVisualService(abc.ABC):
    """
    Abstract Base Class for visual media (image/video frame) generation services.
    """
    @abc.abstractmethod
    async def generate_visual(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        Generates visual asset for scene prompt and returns local output path.
        """
        pass

class PollinationsVisualService(BaseVisualService):
    """
    Free AI Image Generator using Pollinations.ai API with strict 12s timeout and fallback.
    """
    async def generate_visual(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        width, height = (1080, 1920) if aspect_ratio == "9:16" else ((1920, 1080) if aspect_ratio == "16:9" else (1080, 1080))
        
        clean_prompt = prompt.replace("[", "").replace("]", "").strip()
        encoded_prompt = urllib.parse.quote(f"{clean_prompt}, vertical wallpaper, sharp focus, highly detailed")
        seed = random.randint(1000, 999999)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}"

        logger.info(f"[PollinationsVisualService] Fetching image with 12s timeout: '{clean_prompt[:40]}...'")

        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code == 200 and len(res.content) > 5000:
                    with open(output_path, "wb") as f:
                        f.write(res.content)
                    logger.info(f"[PollinationsVisualService] Saved AI image ({len(res.content)} bytes) -> {output_path}")
                    return output_path
        except Exception as e:
            logger.warning(f"[PollinationsVisualService] Pollinations request timed out or failed ({e}). Reverting to clean abstract canvas.")

        return render_fallback_gradient_canvas(output_path, width, height)

class APIVisualService(BaseVisualService):
    """
    Production Visual Generator client with strict 15s timeout wrapper.
    """
    def __init__(self, api_key: str = None, provider: str = "pollinations"):
        self.api_key = api_key or os.getenv("IMAGE_PROVIDER_KEY") or os.getenv("OPENAI_API_KEY")
        self.provider = provider.lower() if provider else "pollinations"

    async def generate_visual(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        width, height = (1080, 1920) if aspect_ratio == "9:16" else ((1920, 1080) if aspect_ratio == "16:9" else (1080, 1080))
        pollinations_service = PollinationsVisualService()
        try:
            return await asyncio.wait_for(
                pollinations_service.generate_visual(prompt, output_path, aspect_ratio),
                timeout=15.0
            )
        except Exception as err:
            logger.warning(f"[APIVisualService] Visual generation timed out after 15s ({err}). Rendering instant gradient background.")
            return render_fallback_gradient_canvas(output_path, width, height)

class MockVisualService(BaseVisualService):
    """
    Instant fallback visual service generating aesthetic dark canvas without text overlays.
    """
    async def generate_visual(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        width, height = (1080, 1920) if aspect_ratio == "9:16" else ((1920, 1080) if aspect_ratio == "16:9" else (1080, 1080))
        return render_fallback_gradient_canvas(output_path, width, height)
