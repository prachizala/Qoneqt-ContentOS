import os
import pytest
import subprocess
from video_engine.stock_broll import KeywordExtractor, StockVideoClient, StockBRollProcessor
from video_engine.providers import StockBRollVideoProvider, get_video_provider
from backend.app.services.visual_service import MockVisualService

def test_keyword_extraction_filters_stopwords():
    prompt1 = "Cinematic 8k volumetric render of a cyber hacker in a neon server room, slow pan"
    keywords1 = KeywordExtractor.extract_search_keywords(prompt1)
    
    assert "hacker" in keywords1 or "cyber" in keywords1 or "server" in keywords1
    assert "8k" not in keywords1
    assert "volumetric" not in keywords1
    assert "cinematic" not in keywords1

    prompt2 = "Photorealistic 3d image showing bitcoin finance growth and cash transactions"
    keywords2 = KeywordExtractor.extract_search_keywords(prompt2)
    assert "bitcoin" in keywords2 or "finance" in keywords2 or "cash" in keywords2
    assert "photorealistic" not in keywords2

def test_stock_video_client_mock_search():
    client = StockVideoClient()
    # Without API keys, returns empty list gracefully
    import asyncio
    res = asyncio.run(client.search_stock_videos("artificial intelligence"))
    assert isinstance(res, list)

def test_stock_broll_crop_and_trim(tmp_path):
    # Synthesize a 4-second raw test video using FFmpeg
    raw_video = os.path.join(tmp_path, "raw_stock.mp4")
    cmd_synth = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=4:size=1920x1080:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        raw_video
    ]
    subprocess.run(cmd_synth, check=True)
    assert os.path.exists(raw_video)

    processor = StockBRollProcessor()
    cropped_video = os.path.join(tmp_path, "cropped_9_16.mp4")
    
    res = processor.process_and_crop_clip(
        input_video_path=raw_video,
        output_clip_path=cropped_video,
        target_duration=2.5,
        aspect_ratio="9:16",
        fps=30
    )

    assert os.path.exists(res)
    assert os.path.getsize(res) > 1000

    # Probe resolution and duration
    cmd_probe = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,duration",
        "-of", "csv=p=0",
        res
    ]
    probe_out = subprocess.run(cmd_probe, stdout=subprocess.PIPE, text=True).stdout.strip()
    assert "1080,1920" in probe_out

@pytest.mark.asyncio
async def test_stock_broll_provider_fallback(tmp_path):
    img_service = MockVisualService()
    img_path = os.path.join(tmp_path, "test_frame.png")
    await img_service.generate_visual("Quantum neural core", img_path)

    provider = StockBRollVideoProvider()
    clip_output = os.path.join(tmp_path, "broll_clip.mp4")

    # Should fall back cleanly to local motion when stock API is not configured
    res_clip = provider.generate_motion_clip_sync(
        image_path=img_path,
        motion_prompt="High speed data streams in quantum mainframe",
        duration=2.0,
        output_path=clip_output,
        aspect_ratio="9:16"
    )

    assert os.path.exists(res_clip)
    assert os.path.getsize(res_clip) > 1000

def test_factory_get_video_provider():
    p_veo = get_video_provider("veo")
    assert p_veo is not None
    p_broll = get_video_provider("stock")
    assert isinstance(p_broll, StockBRollVideoProvider)
