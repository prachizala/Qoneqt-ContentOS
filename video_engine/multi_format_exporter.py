import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

EXPORT_PROFILES: Dict[str, Dict[str, Any]] = {
    "9:16": {
        "name": "Vertical (Reels / Shorts / TikTok)",
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "ass_play_res_x": 1080,
        "ass_play_res_y": 1920,
        "ass_margin_v": 260,
    },
    "16:9": {
        "name": "Horizontal (YouTube / Desktop)",
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "ass_play_res_x": 1920,
        "ass_play_res_y": 1080,
        "ass_margin_v": 110,
    },
    "1:1": {
        "name": "Square (LinkedIn / Instagram Feed)",
        "width": 1080,
        "height": 1080,
        "aspect_ratio": "1:1",
        "ass_play_res_x": 1080,
        "ass_play_res_y": 1080,
        "ass_margin_v": 120,
    }
}

class MultiFormatExportException(Exception):
    """Exception raised when multi-format conversion fails."""
    pass

class MultiFormatExporter:
    """
    Automated Multi-Format Video Exporter for FFmpeg / Remotion.
    Supports 9:16 Vertical, 16:9 Horizontal, and 1:1 Square formats.
    Applies auto-centering and blurred background letterbox fill when converting vertical video to horizontal/square formats.
    """
    def __init__(self, fps: int = 30):
        self.fps = fps

    def build_blurred_canvas_filter(
        self,
        target_width: int,
        target_height: int,
        blur_radius: int = 20,
        blur_power: int = 5,
        dim_factor: float = -0.15
    ) -> str:
        """
        Builds FFmpeg filter_complex that:
        1. Takes input stream and splits into background and foreground streams.
        2. Scales and crops background stream to fill target dimensions with heavy boxblur and dimming.
        3. Scales foreground stream to fit target dimensions preserving aspect ratio.
        4. Overlays foreground centered over the blurred background canvas.
        """
        filter_str = (
            f"[0:v]split=2[bg_src][fg_src];"
            # Background: scale to cover canvas, boxblur, dim
            f"[bg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},"
            f"boxblur={blur_radius}:{blur_power},"
            f"eq=brightness={dim_factor}:contrast=0.9[bg_blurred];"
            # Foreground: scale to fit canvas preserving aspect ratio
            f"[fg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease[fg_scaled];"
            # Centered overlay
            f"[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2[vout]"
        )
        return filter_str

    def convert_format(
        self,
        input_video_path: str,
        output_video_path: str,
        target_format: str = "16:9"
    ) -> str:
        """
        Converts an input video (typically 9:16 vertical) into the requested format (16:9, 1:1, or 9:16).
        """
        if not os.path.exists(input_video_path):
            raise MultiFormatExportException(f"Input video not found: {input_video_path}")

        profile = EXPORT_PROFILES.get(target_format)
        if not profile:
            raise MultiFormatExportException(f"Unsupported format '{target_format}'. Supported: {list(EXPORT_PROFILES.keys())}")

        Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)
        width = profile["width"]
        height = profile["height"]

        if target_format == "9:16":
            # Direct 9:16 vertical pass or smart scale
            vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={self.fps}"
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video_path,
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                output_video_path
            ]
        else:
            # 16:9 or 1:1 with blurred background fill
            filter_complex = self.build_blurred_canvas_filter(width, height)
            cmd = [
                "ffmpeg", "-y",
                "-i", input_video_path,
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-map", "0:a?",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                output_video_path
            ]

        logger.info(f"[MultiFormatExporter] Exporting to {target_format} ({width}x{height}) -> {output_video_path}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            err = f"FFmpeg multi-format export failed for {target_format}:\n{result.stderr}"
            logger.error(err)
            raise MultiFormatExportException(err)

        return output_video_path

    def export_all_formats(
        self,
        input_video_path: str,
        output_dir: str,
        base_name: str = "video"
    ) -> Dict[str, str]:
        """
        Exports input video into all 3 profiles: 9:16, 16:9, and 1:1.
        Returns a dictionary mapping format key to local file path.
        """
        out_paths: Dict[str, str] = {}
        for fmt in ["9:16", "16:9", "1:1"]:
            slug = fmt.replace(":", "_")
            out_file = os.path.join(output_dir, f"{base_name}_{slug}.mp4")
            self.convert_format(input_video_path, out_file, target_format=fmt)
            out_paths[fmt] = out_file

        return out_paths
