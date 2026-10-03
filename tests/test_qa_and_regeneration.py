import os
import uuid
import pytest
from backend.app.services.qa_service import QAService
from backend.app.services.regeneration_service import SceneRegenerationService
from backend.app.services.tts_service import MockTTSService
from backend.app.services.visual_service import MockVisualService
from backend.app.models.models import Project, Script, Scene, ProjectStatus, QASimpleStatus, SceneStatus
from video_engine.renderer import VideoRenderer
from video_engine.subtitles import create_ass_subtitles

@pytest.mark.asyncio
async def test_qa_service_evaluation(tmp_path):
    os.environ["USE_MOCK_AI"] = "true"
    qa_service = QAService()

    proj_id = uuid.uuid4()
    video_file = os.path.join(tmp_path, "sample_video.mp4")

    # Render a small mock vertical video for test using VideoRenderer
    img1 = os.path.join(tmp_path, "frame.png")
    aud1 = os.path.join(tmp_path, "voice.mp3")
    sub1 = os.path.join(tmp_path, "sub.ass")

    await MockVisualService().generate_visual("Scene test visual prompt", img1)
    await MockTTSService().generate_speech("Testing voice narration audio", aud1)
    create_ass_subtitles([{"narration": "Testing voice narration audio", "duration": 2.5}], sub1)

    renderer = VideoRenderer(temp_dir=str(tmp_path))
    renderer.render_vertical_video(
        scene_assets=[{"image_path": img1, "duration": 2.5}],
        audio_paths=[aud1],
        subtitle_ass_path=sub1,
        output_video_path=video_file
    )

    assert os.path.exists(video_file)

    script_data = {
        "title": "Quantum Computing 2026",
        "hook": "Did you know this about quantum tech?",
        "scenes": [{"caption": "Testing voice narration audio"}]
    }

    qa_result = await qa_service.evaluate_video(
        project_id=proj_id,
        video_path=video_file,
        script_data=script_data,
        target_duration=2
    )

    assert qa_result.technical_status in (QASimpleStatus.PASS, QASimpleStatus.FAIL)
    assert qa_result.content_status == QASimpleStatus.PASS
    assert isinstance(qa_result.issues, list)

@pytest.mark.asyncio
async def test_scene_regeneration(tmp_path):
    os.environ["USE_MOCK_AI"] = "true"
    storage_dir = os.path.join(tmp_path, "storage")

    proj_id = uuid.uuid4()
    scene_id = uuid.uuid4()

    # Setup dummy project and scene mock database structure
    scene = Scene(
        id=scene_id,
        project_id=proj_id,
        script_id=uuid.uuid4(),
        scene_number=1,
        duration=3.0,
        narration="Original narration text.",
        visual_prompt="Original visual prompt.",
        caption="Original caption.",
        transition="fade",
        status=SceneStatus.COMPLETED
    )

    project = Project(
        id=proj_id,
        topic="AI Technology",
        status=ProjectStatus.GENERATING,
        duration=3
    )
    project.scenes = [scene]
    project.script = Script(
        id=uuid.uuid4(),
        project_id=proj_id,
        title="AI Tech Overview",
        hook="Check out AI!",
        body="Body text",
        cta="Follow for more"
    )

    class MockAsyncSession:
        def __init__(self, project):
            self.project = project
            self.committed = False
        def add(self, obj): pass
        async def commit(self): self.committed = True
        async def execute(self, stmt):
            class ExecResult:
                def __init__(self, proj): self.proj = proj
                def scalar_one_or_none(self): return self.proj
            return ExecResult(self.project)

        async def close(self): pass

    db_session = MockAsyncSession(project)

    regen_service = SceneRegenerationService(
        tts_service=MockTTSService(),
        visual_service=MockVisualService(),
        renderer=VideoRenderer(temp_dir=storage_dir),
        qa_service=QAService(),
        storage_dir=storage_dir
    )

    res = await regen_service.regenerate_single_scene(
        project_id=proj_id,
        scene_id=scene_id,
        new_prompt="Updated futuristic AI core visual prompt",
        db_session=db_session
    )

    assert res["project_id"] == str(proj_id)
    assert res["scene_id"] == str(scene_id)
    assert os.path.exists(res["output_video_path"])
    assert res["project_status"] == ProjectStatus.READY_FOR_REVIEW.value
    assert db_session.committed is True
