import os
import uuid
import datetime
import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QoneqtPublisher:
    """
    Publisher client for uploading media assets and creating posts on the Qoneqt Global Feed API.
    """
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = (api_url or os.getenv("QONEQT_API_URL", "https://api.qoneqt.com/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("QONEQT_API_KEY", "mock_key")
        
        self.mock_mode = (
            not self.api_key or
            self.api_key.lower() in ("mock", "mock_key", "mock_qoneqt_api_key") or
            self.api_key.startswith("mock_") or
            os.getenv("USE_MOCK_AI", "true").lower() in ("true", "1", "yes")
        )

    async def upload_video(self, file_path: str) -> Dict[str, str]:
        """
        Streams MP4 video file to Qoneqt media upload endpoint via multipart/form-data.
        """
        if self.mock_mode or not os.path.exists(file_path):
            logger.info(f"[QoneqtPublisher] Mock Mode active. Simulating video upload for: {file_path}")
            media_id = f"qoneqt_media_{uuid.uuid4().hex[:10]}"
            return {
                "media_id": media_id,
                "media_url": f"https://cdn.qoneqt.com/media/{media_id}.mp4"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "video/mp4")}
                response = await client.post(
                    f"{self.api_url}/media/upload",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "media_id": data.get("media_id", f"qoneqt_media_{uuid.uuid4().hex[:8]}"),
                    "media_url": data.get("media_url", "")
                }

    async def publish_to_global_feed(
        self,
        title: str,
        caption: str,
        media_id: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Posts video payload to Qoneqt global feed creation endpoint.
        Implements exponential backoff retry (3 attempts) on network or 5xx server errors.
        """
        tags = tags or ["#AIContent", "#QoneqtShorts"]
        
        if self.mock_mode:
            logger.info(f"[QoneqtPublisher] Mock Mode active. Simulating Global Feed post '{title}' (Media ID: {media_id})")
            post_id = f"qoneqt_post_{uuid.uuid4().hex[:10]}"
            return {
                "post_id": post_id,
                "feed_url": f"https://qoneqt.com/feed/post/{post_id}",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }

        payload = {
            "title": title,
            "caption": caption,
            "media_id": media_id,
            "tags": tags
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        max_retries = 3
        backoff_delay = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.api_url}/feed/posts",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code in (502, 503, 504) and attempt < max_retries:
                        logger.warning(
                            f"[QoneqtPublisher] Attempt {attempt} failed with HTTP {response.status_code}. "
                            f"Retrying in {backoff_delay}s..."
                        )
                        await asyncio.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue

                    response.raise_for_status()
                    data = response.json()
                    post_id = data.get("post_id", f"qoneqt_post_{uuid.uuid4().hex[:8]}")
                    return {
                        "post_id": post_id,
                        "feed_url": data.get("feed_url", f"https://qoneqt.com/feed/post/{post_id}"),
                        "timestamp": data.get("timestamp", datetime.datetime.utcnow().isoformat())
                    }
            except (httpx.HTTPStatusError, httpx.RequestError) as err:
                if attempt == max_retries:
                    logger.error(f"[QoneqtPublisher] Final attempt {attempt} failed: {err}")
                    raise err
                logger.warning(f"[QoneqtPublisher] Network error on attempt {attempt}: {err}. Retrying in {backoff_delay}s...")
                await asyncio.sleep(backoff_delay)
                backoff_delay *= 2

        raise RuntimeError("Publish to Qoneqt Global Feed failed after max retries.")
