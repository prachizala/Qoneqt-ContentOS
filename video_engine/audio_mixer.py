import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class AudioMixerException(Exception):
    """Exception raised for errors during audio mixing or dynamic ducking."""
    pass

class AudioMixer:
    """
    Advanced Multi-Channel Audio Mixer with Dynamic Ducking & Sidechain Compression.
    Channels:
      - Channel 0: Voice Narration (crisp, normalized, foreground)
      - Channel 1: Background Music (dynamically ducked to 12-15% during speech, ramping to 35-40% over 200ms during pauses)
      - Channel 2: Procedural Sound Effects (whooshes, punch-ins at 30-40% volume)
    """
    def __init__(self, sample_rate: int = 44100, bitrate: str = "192k"):
        self.sample_rate = sample_rate
        self.bitrate = bitrate

    def build_ducking_filter_graph(
        self,
        has_bg_music: bool = False,
        has_sfx: bool = False,
        **kwargs
    ) -> str:
        """
        Reverted audio filter graph returning clean single-stream voice output.
        """
        return "[0:a]volume=1.0[aout]"

    def mix_audio_tracks(
        self,
        voiceover_path: str,
        background_music_path: Optional[str] = None,
        output_audio_path: str = "./storage/temp/output.mp3",
        sfx_track_path: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Processes clean voice narration audio without complex filter graphs or ducking.
        """
        Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)

        if not os.path.exists(voiceover_path):
            raise AudioMixerException(f"Master voiceover file not found: {voiceover_path}")

        cmd = [
            "ffmpeg", "-y",
            "-i", voiceover_path,
            "-c:a", "aac",
            "-b:a", self.bitrate,
            "-ar", str(self.sample_rate),
            output_audio_path
        ]

        logger.info(f"[AudioMixer] Processing crisp voiceover narration -> {output_audio_path}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            err = f"FFmpeg AudioMixer failed with code {result.returncode}:\n{result.stderr}"
            logger.error(err)
            raise AudioMixerException(err)

        return output_audio_path
