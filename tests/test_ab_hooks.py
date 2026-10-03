import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.database import Base, get_db
from backend.app.models.models import Project, Script, Scene, SceneStatus, ProjectStatus
from backend.main import app
from ai.agents.scriptwriter import ScriptAgent, HookVariations
from ai.agents.researcher import ResearchResult

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_qoneqt.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
from backend.app.models.models import Project, Script, Scene, Asset, Video, QAResult, Publication  # noqa: F401
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.mark.asyncio
async def test_ab_hook_generation():
    agent = ScriptAgent()
    research = ResearchResult(
        core_concept="Autonomous AI Agents in Cybersecurity",
        key_facts=[
            "Over 85% of cyber attacks in 2026 occur in sub-second timeframes.",
            "Autonomous agents reduce incident resolution time by 90%."
        ],
        hook_angles=["Stop scrolling! Cyber warfare changed forever."],
        suggested_cta="Deploy your autonomous security copilot today."
    )

    script_result = await agent.write_script(
        research=research,
        duration=30,
        style="cinematic",
        tone="Viral / Hook Driven"
    )

    assert script_result.title is not None
    assert script_result.hook is not None
    assert script_result.hook_variations is not None

    hooks = script_result.hook_variations
    # Verify 3 distinct hooks
    assert hasattr(hooks, "hook_a") and len(hooks.hook_a) > 10
    assert hasattr(hooks, "hook_b") and len(hooks.hook_b) > 10
    assert hasattr(hooks, "hook_c") and len(hooks.hook_c) > 10

    # Verify distinct styles
    assert "stop" in hooks.hook_a.lower() or "ignoring" in hooks.hook_a.lower()
    assert "90%" in hooks.hook_b or "%" in hooks.hook_b
    assert "truth" in hooks.hook_c.lower() or "secret" in hooks.hook_c.lower() or "hidden" in hooks.hook_c.lower()

@pytest.mark.asyncio
async def test_select_ab_hook_endpoint():
    app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    proj_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        project = Project(
            id=proj_id,
            topic="A/B Hook Testing Project",
            duration=30,
            status=ProjectStatus.READY_FOR_REVIEW
        )
        session.add(project)
        await session.flush()

        script = Script(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="A/B Hook Video",
            hook="Original Hook A: Stop doing this!",
            body="Body narration text",
            cta="Follow for more",
            raw_json={
                "hook_variations": {
                    "hook_a": "Hook A: Stop doing this in 2026!",
                    "hook_b": "Hook B: 90% of engineers don't know this!",
                    "hook_c": "Hook C: The dark truth about coding."
                }
            }
        )
        session.add(script)
        await session.flush()

        scene1 = Scene(
            id=uuid.uuid4(),
            project_id=proj_id,
            script_id=script.id,
            scene_number=1,
            duration=5.0,
            narration="Original Hook A: Stop doing this!",
            visual_prompt="Cyber command center",
            transition="fade",
            status=SceneStatus.COMPLETED
        )
        session.add(scene1)
        await session.commit()

    # Call select hook endpoint with hook_b
    resp = client.post(
        f"/api/projects/{proj_id}/hook",
        json={"hook_key": "hook_b"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["selected_hook"] == "Hook B: 90% of engineers don't know this!"

    # Verify project details reflection
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 200
    proj_data = get_res.json()
    assert proj_data["script"]["hook"] == "Hook B: 90% of engineers don't know this!"
    assert proj_data["scenes"][0]["narration"] == "Hook B: 90% of engineers don't know this!"
