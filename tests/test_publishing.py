import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.database import Base, get_db
from backend.app.models.models import Project, Script, Video, ProjectStatus, VideoStatus
from integrations.qoneqt import QoneqtPublisher
from backend.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.mark.asyncio
async def test_qoneqt_publisher_mock():
    os.environ["QONEQT_API_KEY"] = "mock_key"
    publisher = QoneqtPublisher()

    upload_res = await publisher.upload_video("test_video.mp4")
    assert "media_id" in upload_res
    assert upload_res["media_id"].startswith("qoneqt_media_")

    publish_res = await publisher.publish_to_global_feed(
        title="Test Short Video Title",
        caption="Check out this test short video!",
        media_id=upload_res["media_id"],
        tags=["#AI", "#Qoneqt"]
    )
    assert "post_id" in publish_res
    assert publish_res["post_id"].startswith("qoneqt_post_")
    assert "https://qoneqt.com/feed/post/" in publish_res["feed_url"]

@pytest.mark.asyncio
async def test_publish_endpoint_workflow(tmp_path):
    app.dependency_overrides[get_db] = override_get_db
    os.environ["QONEQT_API_KEY"] = "mock_key"

    proj_id = uuid.uuid4()
    dummy_video_path = os.path.join(tmp_path, "rendered.mp4")
    with open(dummy_video_path, "wb") as f:
        f.write(b"mock video binary content")

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        proj = Project(
            id=proj_id,
            topic="Next-Gen AI Publishing",
            status=ProjectStatus.APPROVED,
            duration=30
        )
        script = Script(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Next-Gen AI Video",
            hook="See how AI publishes to Qoneqt!",
            body="Body text",
            cta="Follow for more"
        )
        vid = Video(
            id=uuid.uuid4(),
            project_id=proj_id,
            file_path=dummy_video_path,
            duration=30.0,
            resolution="1080x1920",
            status=VideoStatus.READY
        )
        session.add(proj)
        session.add(script)
        session.add(vid)
        await session.commit()

    response = client.post(f"/api/projects/{proj_id}/publish")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ProjectStatus.PUBLISHED.value
    assert "publication" in data
    assert data["publication"]["platform"] == "QONEQT"
    assert data["publication"]["post_id"].startswith("qoneqt_post_")
