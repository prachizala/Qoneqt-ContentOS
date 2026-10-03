import os
import abc
import json
import logging
import asyncio
import subprocess
import httpx
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

def get_audio_file_duration(file_path: str) -> float:
    """
    Calculates exact duration of audio file (MP3/WAV/AAC) using ffprobe CLI first,
    then mutagen, then byte-rate estimation fallback.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return 0.0

    # 1. High-precision ffprobe duration inspection
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and res.stdout.strip():
            dur = float(res.stdout.strip())
            if dur > 0.05:
                return round(dur, 3)
    except Exception:
        pass

    # 2. Mutagen MP3 header inspection
    try:
        audio = MP3(file_path)
        if audio.info and audio.info.length and audio.info.length > 0:
            return round(float(audio.info.length), 3)
    except Exception:
        pass

    # 3. File size fallback
    file_size = os.path.getsize(file_path)
    return max(1.5, round(file_size / 16000.0, 2))

def pad_audio_to_duration(input_path: str, target_duration: float, output_path: str) -> str:
    """
    Pads an audio file with trailing silence to exactly match target_duration,
    preventing abrupt audio cut-offs and maintaining zero timeline drift in multi-scene compositing.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    curr_dur = get_audio_file_duration(input_path)
    
    if curr_dur >= target_duration - 0.05:
        # If audio is already long enough or target is identical, just copy or trim
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-t", str(target_duration),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            "-ar", "44100",
            output_path
        ]
    else:
        # Pad with silence up to target_duration
        pad_needed = max(0.1, target_duration - curr_dur)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", f"apad=pad_dur={pad_needed:.3f}",
            "-t", str(target_duration),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            "-ar", "44100",
            output_path
        ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0 or not os.path.exists(output_path):
        logger.warning(f"[pad_audio_to_duration] FFmpeg pad failed ({res.stderr}). Using input file directly.")
        return input_path
    return output_path

class BaseTTSService(abc.ABC):
    """
    Abstract Base Class for Text-to-Speech (TTS) synthesis services.
    """
    @abc.abstractmethod
    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> float:
        """
        Synthesizes text into audio and returns the exact audio duration in seconds.
        """
        pass

    async def generate_speech_with_metadata(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes text into audio and returns duration plus word-level timing metadata.
        """
        duration = await self.generate_speech(text, output_path, voice, target_duration)
        words = text.strip().split()
        word_timings = []
        if words and duration > 0:
            avg_dur = duration / len(words)
            for idx, w in enumerate(words):
                st = round(idx * avg_dur, 3)
                en = round((idx + 1) * avg_dur, 3)
                word_timings.append({
                    "word": w,
                    "start": st,
                    "end": en,
                    "duration": round(en - st, 3)
                })
        return {
            "duration": duration,
            "word_timings": word_timings,
            "audio_path": output_path
        }

class EdgeTTSService(BaseTTSService):
    """
    Production TTS implementation using edge-tts (Microsoft Edge Neural Voice engine).
    Captures word-level alignment boundaries directly from the TTS stream and includes
    automatic retries to ensure no dropped/empty audio frames.
    """
    async def generate_speech_with_metadata(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        max_attempts = 2

        async def _stream_edge_tts():
            import edge_tts
            logger.info(f"[EdgeTTSService] Synthesizing voice='{voice}' -> '{output_path}'")
            communicate = edge_tts.Communicate(text, voice, boundary="WordBoundary")
            word_timings: List[Dict[str, Any]] = []

            with open(output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start_sec = chunk["offset"] / 10_000_000.0
                        dur_sec = chunk["duration"] / 10_000_000.0
                        word_timings.append({
                            "word": chunk.get("text", ""),
                            "start": round(start_sec, 3),
                            "duration": round(dur_sec, 3),
                            "end": round(start_sec + dur_sec, 3)
                        })

            if os.path.exists(output_path) and os.path.getsize(output_path) > 800:
                duration = get_audio_file_duration(output_path)
                if duration > 0.3:
                    if not word_timings:
                        words = text.strip().split()
                        if words:
                            avg_dur = duration / len(words)
                            for idx, w in enumerate(words):
                                st = round(idx * avg_dur, 3)
                                en = round((idx + 1) * avg_dur, 3)
                                word_timings.append({
                                    "word": w,
                                    "start": st,
                                    "end": en,
                                    "duration": round(en - st, 3)
                                })
                    return {
                        "duration": duration,
                        "word_timings": word_timings,
                        "audio_path": output_path
                    }
            raise RuntimeError("EdgeTTS produced empty/invalid audio file")

        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.wait_for(_stream_edge_tts(), timeout=12.0)
            except Exception as e:
                logger.warning(f"[EdgeTTSService] Attempt {attempt} failed or timed out for '{output_path}': {e}")
                await asyncio.sleep(0.3)

        logger.warning(f"[EdgeTTSService] All attempts failed for text: '{text[:40]}...'. Falling back to MockTTSService.")
        mock_tts = MockTTSService()
        return await mock_tts.generate_speech_with_metadata(text, output_path, voice, target_duration=target_duration)

    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> float:
        res = await self.generate_speech_with_metadata(text, output_path, voice, target_duration)
        return res["duration"]

class ElevenLabsTTSService(BaseTTSService):
    """
    Production TTS Provider using ElevenLabs REST API (ELEVENLABS_API_KEY / XI_API_KEY).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY") or os.getenv("XI_API_KEY")

    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "21m00Tcm4TlvDq8ikWAM",
        target_duration: Optional[float] = None
    ) -> float:
        res = await self.generate_speech_with_metadata(text, output_path, voice, target_duration)
        return res["duration"]

    async def generate_speech_with_metadata(
        self,
        text: str,
        output_path: str,
        voice: str = "21m00Tcm4TlvDq8ikWAM",
        target_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if not self.api_key:
            fallback = EdgeTTSService()
            return await fallback.generate_speech_with_metadata(text, output_path, voice, target_duration)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(output_path, "wb") as f:
                        f.write(res.content)
                    duration = get_audio_file_duration(output_path)
                    words = text.strip().split()
                    avg_dur = duration / max(1, len(words))
                    word_timings = [
                        {"word": w, "start": round(i * avg_dur, 3), "end": round((i + 1) * avg_dur, 3), "duration": round(avg_dur, 3)}
                        for i, w in enumerate(words)
                    ]
                    return {"duration": duration, "word_timings": word_timings, "audio_path": output_path}
        except Exception as e:
            logger.warning(f"[ElevenLabsTTSService] API error ({e}). Falling back to EdgeTTS.")

        fallback = EdgeTTSService()
        return await fallback.generate_speech_with_metadata(text, output_path, voice, target_duration)

class OpenAITTSService(BaseTTSService):
    """
    Production TTS Provider using OpenAI Audio Speech API (OPENAI_API_KEY).
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "alloy",
        target_duration: Optional[float] = None
    ) -> float:
        res = await self.generate_speech_with_metadata(text, output_path, voice, target_duration)
        return res["duration"]

    async def generate_speech_with_metadata(
        self,
        text: str,
        output_path: str,
        voice: str = "alloy",
        target_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if not self.api_key or self.api_key == "mock_openai_api_key":
            fallback = EdgeTTSService()
            return await fallback.generate_speech_with_metadata(text, output_path, voice, target_duration)

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice if voice in ("alloy", "echo", "fable", "onyx", "nova", "shimmer") else "alloy"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200 and len(res.content) > 1000:
                    with open(output_path, "wb") as f:
                        f.write(res.content)
                    duration = get_audio_file_duration(output_path)
                    words = text.strip().split()
                    avg_dur = duration / max(1, len(words))
                    word_timings = [
                        {"word": w, "start": round(i * avg_dur, 3), "end": round((i + 1) * avg_dur, 3), "duration": round(avg_dur, 3)}
                        for i, w in enumerate(words)
                    ]
                    return {"duration": duration, "word_timings": word_timings, "audio_path": output_path}
        except Exception as e:
            logger.warning(f"[OpenAITTSService] API error ({e}). Falling back to EdgeTTS.")

        fallback = EdgeTTSService()
        return await fallback.generate_speech_with_metadata(text, output_path, voice, target_duration)

class MockTTSService(BaseTTSService):
    """
    Mock TTS service for offline development and unit tests.
    Generates audible tone/synth MP3 audio files matching narration length.
    """
    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> float:
        res = await self.generate_speech_with_metadata(text, output_path, voice, target_duration)
        return res["duration"]

    async def generate_speech_with_metadata(
        self,
        text: str,
        output_path: str,
        voice: str = "en-US-ChristopherNeural",
        target_duration: Optional[float] = None
    ) -> Dict[str, Any]:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        words = text.strip().split()
        estimated_duration = max(2.5, round(len(words) / 2.3, 2))
        duration = float(target_duration) if target_duration and target_duration > 0 else estimated_duration

        logger.info(f"[MockTTSService] Synthesizing audible mock speech track ({duration:.2f}s) -> {output_path}")

        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"sine=frequency=520:duration={duration}",
            "-af", "volume=0.4",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            "-ar", "44100",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0 or not os.path.exists(output_path):
            silent_frame = b"\xff\xfb\x90\xc4" + b"\x00" * 413
            frame_count = int(duration * 38.28)
            with open(output_path, "wb") as f:
                for _ in range(max(10, frame_count)):
                    f.write(silent_frame)

        avg_dur = duration / max(1, len(words))
        word_timings = [
            {"word": w, "start": round(i * avg_dur, 3), "end": round((i + 1) * avg_dur, 3), "duration": round(avg_dur, 3)}
            for i, w in enumerate(words)
        ]

        return {
            "duration": duration,
            "word_timings": word_timings,
            "audio_path": output_path
        }

def get_tts_provider(provider_name: Optional[str] = None) -> BaseTTSService:
    """
    Factory function for TTS Provider selection.
    Supported options: 'edge' (Microsoft Edge Neural TTS), 'elevenlabs', 'openai', 'mock'.
    """
    name = (provider_name or os.getenv("TTS_PROVIDER", "edge")).lower()
    if name in ("elevenlabs", "eleven"):
        return ElevenLabsTTSService()
    elif name in ("openai", "gpt"):
        return OpenAITTSService()
    elif name in ("mock", "test"):
        return MockTTSService()
    else:
        return EdgeTTSService()
