import os
import wave
import pytest
from video_engine.sound_design import SoundDesignEngine
from video_engine.audio_mixer import AudioMixer, AudioMixerException
from video_engine.renderer import VideoRenderer
from backend.app.services.visual_service import MockVisualService
from backend.app.services.tts_service import MockTTSService
from video_engine.subtitles import create_ass_subtitles

def test_procedural_whoosh_generation(tmp_path):
    engine = SoundDesignEngine(sample_rate=44100)
    whoosh_path = os.path.join(tmp_path, "test_whoosh.wav")
    
    res = engine.generate_procedural_whoosh(
        output_path=whoosh_path,
        duration=0.35,
        peak_volume=0.35
    )

    assert os.path.exists(res)
    assert os.path.getsize(res) > 500

    with wave.open(res, "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 44100
        frames = w.getnframes()
        duration = frames / 44100
        assert abs(duration - 0.35) < 0.05

def test_procedural_punch_generation(tmp_path):
    engine = SoundDesignEngine(sample_rate=44100)
    punch_path = os.path.join(tmp_path, "test_punch.wav")

    res = engine.generate_procedural_punch(
        output_path=punch_path,
        duration=0.18,
        peak_volume=0.30
    )

    assert os.path.exists(res)
    assert os.path.getsize(res) > 300

    with wave.open(res, "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == 44100

def test_calculate_sfx_trigger_events():
    engine = SoundDesignEngine()
    scene_assets = [
        {"duration": 3.0, "narration": "First scene start."},
        {"duration": 4.0, "narration": "Second scene continuation."}
    ]

    events = engine.calculate_sfx_trigger_events(scene_assets, None)
    assert len(events) == 0

def test_composite_sfx_track_rendering(tmp_path):
    engine = SoundDesignEngine(sample_rate=44100)
    events = []
    out_sfx = os.path.join(tmp_path, "sfx_master.wav")
    res = engine.render_composite_sfx_track(
        sfx_events=events,
        total_duration=5.0,
        output_track_path=out_sfx,
        work_dir=str(tmp_path)
    )

    assert os.path.exists(res)
    assert os.path.getsize(res) > 100

def test_audio_mixer_ducking_filter_graph():
    mixer = AudioMixer()

    graph = mixer.build_ducking_filter_graph()
    assert "[0:a]volume=1.0[aout]" in graph

@pytest.mark.asyncio
async def test_full_video_render_with_ducking_and_sfx(tmp_path):
    img_service = MockVisualService()
    tts_service = MockTTSService()

    img1 = os.path.join(tmp_path, "scene_1.png")
    img2 = os.path.join(tmp_path, "scene_2.png")
    await img_service.generate_visual("Scene 1", img1)
    await img_service.generate_visual("Scene 2", img2)

    aud1 = os.path.join(tmp_path, "scene_1.mp3")
    aud2 = os.path.join(tmp_path, "scene_2.mp3")
    dur1 = await tts_service.generate_speech("First scene high impact voiceover.", aud1)
    dur2 = await tts_service.generate_speech("Second scene high impact voiceover.", aud2)

    scene_assets = [
        {"image_path": img1, "duration": dur1},
        {"image_path": img2, "duration": dur2}
    ]

    subtitle_ass = os.path.join(tmp_path, "subtitles.ass")
    create_ass_subtitles(
        [
            {"narration": "First scene high impact voiceover.", "duration": dur1},
            {"narration": "Second scene high impact voiceover.", "duration": dur2}
        ],
        subtitle_ass
    )

    output_video = os.path.join(tmp_path, "output", "final_ducked_video.mp4")
    renderer = VideoRenderer(temp_dir=str(tmp_path))

    res_video_path = renderer.render_vertical_video(
        scene_assets=scene_assets,
        audio_paths=[aud1, aud2],
        subtitle_ass_path=subtitle_ass,
        output_video_path=output_video
    )

    assert os.path.exists(res_video_path)
    assert os.path.getsize(res_video_path) > 0

def test_viral_ass_subtitles_with_emojis(tmp_path):
    subtitle_ass = os.path.join(tmp_path, "viral_subtitles.ass")
    scenes = [
        {
            "narration": "AI robots generate huge money and growth.",
            "duration": 3.5,
            "word_timings": [
                {"word": "AI", "start": 0.0, "end": 0.3},
                {"word": "robots", "start": 0.3, "end": 0.7},
                {"word": "generate", "start": 0.7, "end": 1.2},
                {"word": "huge", "start": 1.2, "end": 1.6},
                {"word": "money", "start": 1.6, "end": 2.2},
                {"word": "and", "start": 2.2, "end": 2.4},
                {"word": "growth", "start": 2.4, "end": 3.0}
            ]
        }
    ]

    res_path = create_ass_subtitles(scenes, subtitle_ass)
    assert os.path.exists(res_path)

    with open(res_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify Hormozi style yellow highlight in styles
    assert "&H0000E6FF" in content  # Bright Yellow BGR
    assert r"{\t(0,100,\fscx110\fscy110)}" in content
    # Verify emojis injected
    assert "🤖" in content or "💰" in content or "🚀" in content

