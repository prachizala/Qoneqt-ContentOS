import os
import pytest
from video_engine.subtitles import create_ass_subtitles, seconds_to_ass_timestamp
from video_engine.renderer import VideoRenderer, VideoRenderException
from backend.app.services.visual_service import MockVisualService
from backend.app.services.tts_service import MockTTSService

def test_ass_subtitle_generation(tmp_path):
    output_ass = os.path.join(tmp_path, "subtitles.ass")
    scenes = [
        {"narration": "Stop scrolling and check out this AI video generator!", "duration": 3.0},
        {"narration": "It automatically turns topics into finished videos ready for Qoneqt.", "duration": 4.0}
    ]

    res_path = create_ass_subtitles(scenes, output_ass)

    assert os.path.exists(res_path)
    with open(res_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PlayResX: 1080" in content
    assert "PlayResY: 1920" in content
    assert "MarginV, Encoding" in content
    assert "Stop" in content
    assert r"{\k" in content

@pytest.mark.asyncio
async def test_full_video_rendering(tmp_path):
    img_service = MockVisualService()
    tts_service = MockTTSService()

    img1 = os.path.join(tmp_path, "scene_1.png")
    img2 = os.path.join(tmp_path, "scene_2.png")

    await img_service.generate_visual("Scene 1: Futuristic skyline", img1)
    await img_service.generate_visual("Scene 2: High tech neural interface", img2)

    aud1 = os.path.join(tmp_path, "scene_1.mp3")
    aud2 = os.path.join(tmp_path, "scene_2.mp3")

    dur1 = await tts_service.generate_speech("Scene 1 voiceover text narration.", aud1)
    dur2 = await tts_service.generate_speech("Scene 2 voiceover text narration.", aud2)

    scene_assets = [
        {"image_path": img1, "duration": dur1},
        {"image_path": img2, "duration": dur2}
    ]

    subtitle_ass = os.path.join(tmp_path, "subtitles.ass")
    create_ass_subtitles(
        [
            {"narration": "Scene 1 voiceover text narration.", "duration": dur1},
            {"narration": "Scene 2 voiceover text narration.", "duration": dur2}
        ],
        subtitle_ass
    )

    output_video = os.path.join(tmp_path, "output", "final_video.mp4")
    renderer = VideoRenderer(temp_dir=str(tmp_path))

    res_video_path = renderer.render_vertical_video(
        scene_assets=scene_assets,
        audio_paths=[aud1, aud2],
        subtitle_ass_path=subtitle_ass,
        output_video_path=output_video
    )

    assert os.path.exists(res_video_path)
    assert os.path.getsize(res_video_path) > 0

    thumbnail = os.path.join(tmp_path, "output", "thumbnail.jpg")
    assert os.path.exists(thumbnail)
