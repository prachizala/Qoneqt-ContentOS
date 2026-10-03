import os
import pytest
import subprocess
from video_engine.multi_format_exporter import MultiFormatExporter, EXPORT_PROFILES
from httpx import AsyncClient
from backend.main import app

def test_multi_format_profiles_configuration():
    assert "9:16" in EXPORT_PROFILES
    assert "16:9" in EXPORT_PROFILES
    assert "1:1" in EXPORT_PROFILES

    assert EXPORT_PROFILES["9:16"]["width"] == 1080 and EXPORT_PROFILES["9:16"]["height"] == 1920
    assert EXPORT_PROFILES["16:9"]["width"] == 1920 and EXPORT_PROFILES["16:9"]["height"] == 1080
    assert EXPORT_PROFILES["1:1"]["width"] == 1080 and EXPORT_PROFILES["1:1"]["height"] == 1080

def test_convert_format_horizontal_with_blurred_bg(tmp_path):
    # Synthesize vertical 1080x1920 2-second test video
    raw_vertical = os.path.join(tmp_path, "input_vertical.mp4")
    cmd_synth = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1080x1920:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        raw_vertical
    ]
    subprocess.run(cmd_synth, check=True)
    assert os.path.exists(raw_vertical)

    exporter = MultiFormatExporter()
    
    # 1. Convert to 16:9 Horizontal
    out_16_9 = os.path.join(tmp_path, "output_16_9.mp4")
    res_16_9 = exporter.convert_format(raw_vertical, out_16_9, target_format="16:9")
    assert os.path.exists(res_16_9)

    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        res_16_9
    ]
    probe_out = subprocess.run(cmd_probe, stdout=subprocess.PIPE, text=True).stdout.strip()
    assert "1920,1080" in probe_out

    # 2. Convert to 1:1 Square
    out_1_1 = os.path.join(tmp_path, "output_1_1.mp4")
    res_1_1 = exporter.convert_format(raw_vertical, out_1_1, target_format="1:1")
    assert os.path.exists(res_1_1)

    probe_1_1 = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        res_1_1
    ], stdout=subprocess.PIPE, text=True).stdout.strip()
    assert "1080,1080" in probe_1_1

def test_export_all_formats(tmp_path):
    raw_vertical = os.path.join(tmp_path, "source.mp4")
    cmd_synth = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=1:size=1080x1920:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        raw_vertical
    ]
    subprocess.run(cmd_synth, check=True)

    exporter = MultiFormatExporter()
    exports = exporter.export_all_formats(
        input_video_path=raw_vertical,
        output_dir=str(tmp_path),
        base_name="final"
    )

    assert "9:16" in exports and os.path.exists(exports["9:16"])
    assert "16:9" in exports and os.path.exists(exports["16:9"])
    assert "1:1" in exports and os.path.exists(exports["1:1"])
