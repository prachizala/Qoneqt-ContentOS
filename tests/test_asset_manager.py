import os
import uuid
import pytest
from backend.app.models.models import Scene, SceneStatus
from backend.app.services.tts_service import MockTTSService
from backend.app.services.visual_service import MockVisualService
from backend.app.services.asset_manager import AssetManager

@pytest.mark.asyncio
async def test_mock_tts_service(tmp_path):
    output_path = os.path.join(tmp_path, "test_speech.mp3")
    tts = MockTTSService()
    duration = await tts.generate_speech("Hello world, testing TTS narration generation.", output_path)

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    assert duration >= 2.0

@pytest.mark.asyncio
async def test_mock_visual_service(tmp_path):
    output_path = os.path.join(tmp_path, "test_canvas.png")
    visual = MockVisualService()
    result_path = await visual.generate_visual("A futuristic cinematic city skyline", output_path, aspect_ratio="9:16")

    assert os.path.exists(result_path)
    assert result_path == output_path
    assert os.path.getsize(output_path) > 0

class DummyAsyncSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

@pytest.mark.asyncio
async def test_asset_manager_orchestrator(tmp_path):
    storage_dir = os.path.join(tmp_path, "storage")
    asset_manager = AssetManager(
        tts_service=MockTTSService(),
        visual_service=MockVisualService(),
        storage_dir=storage_dir
    )

    dummy_project_id = uuid.uuid4()
    scene = Scene(
        id=uuid.uuid4(),
        project_id=dummy_project_id,
        script_id=uuid.uuid4(),
        scene_number=1,
        duration=5.0,
        narration="Testing short-form video scene narration step.",
        visual_prompt="Close-up shot of a high-tech glowing AI core",
        caption="Testing AI Core...",
        transition="zoom_in",
        status=SceneStatus.PENDING
    )

    db_session = DummyAsyncSession()

    res = await asset_manager.generate_scene_assets(
        project_id=dummy_project_id,
        scene=scene,
        db_session=db_session
    )

    assert res["scene_number"] == 1
    assert os.path.exists(res["audio_path"])
    assert os.path.exists(res["image_path"])
    assert scene.status == SceneStatus.COMPLETED
    assert scene.duration == res["actual_duration"]
    assert len(db_session.added) == 2
    assert db_session.committed is True
