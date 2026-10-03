import os
import re
import logging
import asyncio
import urllib.parse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# Stop words and stylistic tokens to filter out during keyword extraction
STYLE_STOPWORDS = {
    "cinematic", "photorealistic", "volumetric", "render", "unreal", "engine", "octane",
    "8k", "4k", "resolution", "highly", "detailed", "lighting", "hyperrealistic",
    "sharp", "focus", "wallpaper", "masterpiece", "trending", "artstation", "studio",
    "ambient", "atmospheric", "quality", "clean", "composition", "style", "vertical",
    "ratio", "scene", "showing", "depicting", "featuring", "image", "photo", "video",
    "shot", "camera", "angle", "view", "close", "up", "wide", "slow", "motion",
    "push", "in", "pan", "zoom", "glide", "drift", "a", "an", "the", "with", "and",
    "in", "on", "at", "to", "for", "of", "by", "from", "is", "are"
}

class KeywordExtractor:
    """
    Extracts high-relevance visual entities and action keywords from visual prompts.
    """
    @staticmethod
    def extract_search_keywords(prompt: str, max_keywords: int = 4) -> str:
        if not prompt:
            return "technology abstract"

        # Remove special characters and brackets
        cleaned = re.sub(r"[^\w\s]", " ", prompt.lower())
        words = [w.strip() for w in cleaned.split() if len(w.strip()) > 2]
        
        filtered = [w for w in words if w not in STYLE_STOPWORDS]

        # Prioritize high value domain tokens if present
        domain_prio = ["ai", "cyber", "hacker", "money", "bitcoin", "finance", "robot", "cloud", "server", "security", "code", "future", "network", "quantum", "data"]
        prio_matches = [w for w in filtered if any(dp in w for dp in domain_prio)]
        
        # Deduplicate while preserving order
        seen = set()
        final_keywords: List[str] = []
        for w in (prio_matches + filtered):
            if w not in seen:
                seen.add(w)
                final_keywords.append(w)
            if len(final_keywords) >= max_keywords:
                break

        query = " ".join(final_keywords) if final_keywords else "futuristic technology"
        return query

class StockVideoClient:
    """
    Client for Pexels and Pixabay Stock Video APIs.
    Searches for vertical HD 9:16 video clips with automated fallback.
    """
    def __init__(
        self,
        pexels_api_key: Optional[str] = None,
        pixabay_api_key: Optional[str] = None
    ):
        self.pexels_api_key = pexels_api_key or os.getenv("PEXELS_API_KEY")
        self.pixabay_api_key = pixabay_api_key or os.getenv("PIXABAY_API_KEY")

    async def search_stock_videos(
        self,
        query: str,
        orientation: str = "portrait",
        per_page: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Searches Pexels and Pixabay for matching stock video clips.
        """
        results: List[Dict[str, Any]] = []

        # 1. Try Pexels Video API if API key is provided
        if self.pexels_api_key:
            try:
                headers = {"Authorization": self.pexels_api_key}
                encoded_q = urllib.parse.quote(query)
                url = f"https://api.pexels.com/videos/search?query={encoded_q}&orientation={orientation}&per_page={per_page}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        for v in data.get("videos", []):
                            files = v.get("video_files", [])
                            # Prefer HD portrait files
                            hd_file = next((f for f in files if f.get("quality") == "hd" and f.get("height", 0) >= 1280), None)
                            if not hd_file and files:
                                hd_file = files[0]
                            if hd_file:
                                results.append({
                                    "provider": "pexels",
                                    "id": str(v.get("id")),
                                    "download_url": hd_file.get("link"),
                                    "width": hd_file.get("width"),
                                    "height": hd_file.get("height"),
                                    "duration": v.get("duration", 10)
                                })
            except Exception as e:
                logger.warning(f"[StockVideoClient] Pexels API search error: {e}")

        # 2. Try Pixabay Video API if API key is provided
        if not results and self.pixabay_api_key:
            try:
                encoded_q = urllib.parse.quote(query)
                url = f"https://pixabay.com/api/videos/?key={self.pixabay_api_key}&q={encoded_q}&per_page={per_page}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        for hit in data.get("hits", []):
                            v_urls = hit.get("videos", {})
                            med = v_urls.get("medium") or v_urls.get("large") or v_urls.get("small")
                            if med and med.get("url"):
                                results.append({
                                    "provider": "pixabay",
                                    "id": str(hit.get("id")),
                                    "download_url": med.get("url"),
                                    "width": med.get("width"),
                                    "height": med.get("height"),
                                    "duration": hit.get("duration", 10)
                                })
            except Exception as e:
                logger.warning(f"[StockVideoClient] Pixabay API search error: {e}")

        return results

    async def download_video(self, url: str, target_path: str) -> bool:
        """
        Downloads a video file from remote URL to target_path.
        """
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                    return True
        except Exception as e:
            logger.warning(f"[StockVideoClient] Failed to download stock video from {url}: {e}")
        return False

class StockBRollProcessor:
    """
    Handles downloading, cropping, scaling to 1080x1920 (9:16 vertical),
    and trimming stock footage to exact scene audio durations.
    """
    def __init__(self, stock_client: Optional[StockVideoClient] = None):
        self.stock_client = stock_client or StockVideoClient()

    def process_and_crop_clip(
        self,
        input_video_path: str,
        output_clip_path: str,
        target_duration: float,
        aspect_ratio: str = "9:16",
        fps: int = 30
    ) -> str:
        """
        Crops and trims input stock video to 9:16 1080x1920 (or target aspect ratio)
        and exact target_duration at 30 fps using FFmpeg.
        """
        Path(output_clip_path).parent.mkdir(parents=True, exist_ok=True)
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

        # 9:16 Smart Center Crop filter
        vf_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"fps={fps}"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",  # Loop if stock footage is shorter than target duration
            "-i", input_video_path,
            "-t", str(target_duration),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-an",  # Strip audio track from stock video
            output_clip_path
        ]

        logger.info(f"[StockBRollProcessor] Trimming and cropping stock video -> {output_clip_path} ({target_duration:.2f}s)")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            err = f"FFmpeg stock video crop failed: {result.stderr}"
            logger.error(err)
            raise RuntimeError(err)

        return output_clip_path

    async def fetch_and_prepare_stock_broll(
        self,
        visual_prompt: str,
        target_duration: float,
        output_clip_path: str,
        work_dir: str,
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """
        End-to-end stock B-Roll resolution:
        1. Extracts primary search keywords from prompt.
        2. Queries stock APIs.
        3. Downloads top match.
        4. Crops & trims to 1080x1920 vertical video matching exact scene duration.
        """
        keywords = KeywordExtractor.extract_search_keywords(visual_prompt)
        logger.info(f"[StockBRollProcessor] Searching stock B-roll for keywords: '{keywords}'")

        clips = await self.stock_client.search_stock_videos(keywords, orientation="portrait")
        if not clips:
            # Broader generic tech search retry
            clips = await self.stock_client.search_stock_videos("technology digital abstract", orientation="portrait")

        if clips:
            top_clip = clips[0]
            raw_download_path = os.path.join(work_dir, f"stock_raw_{top_clip['id']}.mp4")
            downloaded = await self.stock_client.download_video(top_clip["download_url"], raw_download_path)

            if downloaded and os.path.exists(raw_download_path) and os.path.getsize(raw_download_path) > 10000:
                return await asyncio.to_thread(
                    self.process_and_crop_clip,
                    raw_download_path,
                    output_clip_path,
                    target_duration,
                    aspect_ratio
                )

        return None
