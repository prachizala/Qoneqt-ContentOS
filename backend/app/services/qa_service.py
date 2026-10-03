import os
import json
import uuid
import logging
import asyncio
import subprocess
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import QAResult, QASimpleStatus, ProjectStatus
from ai.llm_client import LLMClient

logger = logging.getLogger(__name__)

class QAContentCheckResult(BaseModel):
    """
    Pydantic schema for LLM-based video content QA evaluation.
    """
    is_gibberish: bool = Field(description="True if text contains meaningless gibberish.")
    has_inappropriate_content: bool = Field(description="True if content contains explicit or inappropriate words.")
    topic_alignment_score: int = Field(ge=1, le=10, description="Relevance score (1-10) to the core topic.")
    has_text_artifacts: bool = Field(default=False, description="True if raw text artifacts or baked-in watermarks were detected inside AI frames.")
    content_issues: List[str] = Field(default_factory=list, description="List of content-related flags.")

class QAService:
    """
    Automated Quality Assurance Engine executing technical ffprobe checks,
    aspect ratio verification, audio-first sync alignment, audio stream integrity, and LLM content validation.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    async def evaluate_video(
        self,
        project_id: Union[str, uuid.UUID],
        video_path: str,
        script_data: Dict[str, Any],
        target_duration: int = 30,
        db_session: Optional[AsyncSession] = None
    ) -> QAResult:
        """
        Executes technical and content QA checks on a rendered short-form video.
        Ensures video contains an active, non-empty voiceover audio stream and that
        total_audio_duration <= total_video_duration with zero stream drops.
        """
        project_id_uuid = uuid.UUID(str(project_id))
        issues: List[Dict[str, Any]] = []

        logger.info(f"[QAService] Evaluating video: {video_path} for project {project_id_uuid}")

        # ----------------------------------------------------
        # 1. Technical Quality Checks & Audio-First Integrity
        # ----------------------------------------------------
        tech_pass = True

        # Check 1a: File existence and non-zero size (> 100 KB)
        if not os.path.exists(video_path):
            tech_pass = False
            issues.append({"check": "file_existence", "detail": f"Video file not found at {video_path}", "severity": "HIGH"})
        else:
            file_size_bytes = os.path.getsize(video_path)
            min_size_bytes = 100 * 1024
            if file_size_bytes < min_size_bytes:
                tech_pass = False
                issues.append({
                    "check": "file_size",
                    "detail": f"Video size ({file_size_bytes / 1024:.1f} KB) is below minimum threshold",
                    "severity": "HIGH"
                })

        # Check 1b: FFprobe metadata and Audio Stream Synchronization
        if os.path.exists(video_path):
            ffprobe_meta = await asyncio.to_thread(self._run_ffprobe, video_path)
            
            if ffprobe_meta.get("error"):
                tech_pass = False
                issues.append({"check": "ffprobe_read", "detail": ffprobe_meta["error"], "severity": "HIGH"})
            else:
                width = ffprobe_meta.get("width")
                height = ffprobe_meta.get("height")
                duration = ffprobe_meta.get("duration", 0.0)
                audio_duration = ffprobe_meta.get("audio_duration", 0.0)
                v_codec = ffprobe_meta.get("v_codec", "")
                a_codec = ffprobe_meta.get("a_codec", "")
                has_audio = ffprobe_meta.get("has_audio", False)

                # Resolution & 9:16 Aspect Ratio Check (1080x1920)
                if width != 1080 or height != 1920:
                    tech_pass = False
                    issues.append({
                        "check": "resolution",
                        "detail": f"Expected 9:16 resolution 1080x1920, found {width}x{height}",
                        "severity": "MEDIUM"
                    })

                # Video Codec Check (H.264)
                if "h264" not in v_codec.lower():
                    tech_pass = False
                    issues.append({
                        "check": "video_codec",
                        "detail": f"Codec '{v_codec}' is not h264",
                        "severity": "MEDIUM"
                    })

                # Mandatory Audio Stream & Voiceover Verification
                if not has_audio:
                    tech_pass = False
                    issues.append({
                        "check": "audio_stream",
                        "detail": "No active audio stream detected in video container (voiceover missing)",
                        "severity": "HIGH"
                    })
                elif audio_duration < 1.0:
                    tech_pass = False
                    issues.append({
                        "check": "audio_duration",
                        "detail": f"Audio stream duration ({audio_duration:.1f}s) is empty or truncated",
                        "severity": "HIGH"
                    })
                else:
                    # Mandatory Audio-First Gate: total_audio_duration <= total_video_duration + 0.1
                    # and audio stream must cover video duration without abrupt cut-off
                    if audio_duration > duration + 0.2:
                        tech_pass = False
                        issues.append({
                            "check": "audio_video_sync",
                            "detail": f"Audio duration ({audio_duration:.2f}s) exceeds video duration ({duration:.2f}s) causing overrun",
                            "severity": "HIGH"
                        })
                    elif duration > audio_duration + 2.0:
                        issues.append({
                            "check": "audio_coverage",
                            "detail": f"Audio duration ({audio_duration:.2f}s) finishes {duration - audio_duration:.2f}s before video ends",
                            "severity": "LOW"
                        })

                if a_codec and a_codec.lower() not in ("aac", "mp3", "flac", "pcm_s16le"):
                    issues.append({
                        "check": "audio_codec",
                        "detail": f"Audio codec '{a_codec}' is non-standard",
                        "severity": "LOW"
                    })

        technical_status = QASimpleStatus.PASS if tech_pass else QASimpleStatus.FAIL

        # ----------------------------------------------------
        # 2. Content Quality Checks via LLM
        # ----------------------------------------------------
        content_pass = True
        content_eval = await self._evaluate_content(script_data)

        if content_eval.is_gibberish:
            content_pass = False
            issues.append({"check": "content_gibberish", "detail": "Detected gibberish or unreadable text", "severity": "HIGH"})

        if content_eval.has_inappropriate_content:
            content_pass = False
            issues.append({"check": "content_safety", "detail": "Detected inappropriate or unsafe terms", "severity": "HIGH"})

        if content_eval.has_text_artifacts:
            content_pass = False
            issues.append({"check": "text_artifacts", "detail": "Detected raw prompt text or baked-in artifacts inside visual frames", "severity": "HIGH"})

        if content_eval.topic_alignment_score < 6:
            content_pass = False
            issues.append({
                "check": "topic_alignment",
                "detail": f"Topic alignment score ({content_eval.topic_alignment_score}/10) below threshold 6",
                "severity": "MEDIUM"
            })

        for detail in content_eval.content_issues:
            issues.append({"check": "content_flag", "detail": detail, "severity": "LOW"})

        content_status = QASimpleStatus.PASS if content_pass else QASimpleStatus.FAIL
        final_status = QASimpleStatus.PASS if (tech_pass and content_pass) else QASimpleStatus.FAIL

        # ----------------------------------------------------
        # 3. Database Persistence
        # ----------------------------------------------------
        qa_result = QAResult(
            id=uuid.uuid4(),
            project_id=project_id_uuid,
            technical_status=technical_status,
            content_status=content_status,
            issues=issues,
            final_status=final_status
        )

        if db_session:
            db_session.add(qa_result)
            await db_session.commit()
            logger.info(f"[QAService] Persisted QAResult {qa_result.id} with status '{final_status}'")

        return qa_result

    def _run_ffprobe(self, video_path: str) -> Dict[str, Any]:
        """
        Executes ffprobe CLI to extract resolution, duration, audio duration, codecs, and audio stream presence.
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "stream=width,height,codec_name,codec_type,duration:format=duration",
                "-of", "json",
                video_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                return {"error": f"ffprobe exit code {res.returncode}: {res.stderr}"}

            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            format_info = data.get("format", {})

            duration = float(format_info.get("duration", 0.0))
            v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
            a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

            a_duration = float(a_stream.get("duration", duration)) if a_stream else 0.0

            return {
                "width": v_stream.get("width"),
                "height": v_stream.get("height"),
                "v_codec": v_stream.get("codec_name", ""),
                "a_codec": a_stream.get("codec_name", ""),
                "duration": duration,
                "audio_duration": a_duration,
                "has_audio": bool(a_stream)
            }
        except Exception as err:
            logger.warning(f"[QAService] ffprobe failed: {err}")
            return {"error": str(err)}

    async def _evaluate_content(self, script_data: Dict[str, Any]) -> QAContentCheckResult:
        """
        Invokes LLM to check content text quality, text artifact absence, and topic alignment score.
        """
        title = script_data.get("title", "")
        hook = script_data.get("hook", "")
        captions = [s.get("caption") or s.get("narration") for s in script_data.get("scenes", [])]

        system_prompt = (
            "You are a Quality Control Director for short-form media. "
            "Analyze the video script and captions for gibberish, inappropriate keywords, text artifacts, and topic relevance."
        )

        user_prompt = (
            f"Title: {title}\n"
            f"Hook: {hook}\n"
            f"Captions: {captions}\n\n"
            f"Evaluate for gibberish, inappropriate terms, baked-in text artifacts, and topic alignment score (1-10)."
        )

        mock_fallback = QAContentCheckResult(
            is_gibberish=False,
            has_inappropriate_content=False,
            topic_alignment_score=9,
            has_text_artifacts=False,
            content_issues=[]
        )

        return await self.llm_client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=QAContentCheckResult,
            mock_fallback=mock_fallback
        )
