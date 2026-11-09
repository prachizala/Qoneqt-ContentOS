import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.models.models import Project, Script, Scene, ProjectStatus
from backend.main import app
from ai.agents.retention_auditor import RetentionAuditor, RetentionAuditReport

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.mark.asyncio
async def test_retention_auditor_heuristics():
    auditor = RetentionAuditor()
    scenes = [
        {
            "scene_number": 1,
            "duration": 3.0,
            "narration": "Stop scrolling! 99% of developers have no idea how autonomous AI agents actually work.",
            "caption": "Stop scrolling! 99% of developers..."
        },
        {
            "scene_number": 2,
            "duration": 3.5,
            "narration": "In 2026, multi-agent systems coordinate complex software builds in seconds without human bottleneck.",
            "caption": "Multi-agent systems build in seconds."
        },
        {
            "scene_number": 3,
            "duration": 3.5,
            "narration": "The secret lies in asynchronous tool dispatch and state graph reconciliation.",
            "caption": "The secret lies in async dispatch."
        },
        {
            "scene_number": 4,
            "duration": 3.0,
            "narration": "Drop a comment below with your tech stack to get the free architecture guide now!",
            "caption": "Drop a comment below for free guide!"
        }
    ]

    report = await auditor.audit_script(
        title="Autonomous AI Multi-Agent Architecture",
        scenes=scenes,
        target_duration=13.0,
        topic="Autonomous AI"
    )

    assert isinstance(report, RetentionAuditReport)
    assert report.overall_score >= 70
    assert report.grade in ("VIRAL_OUTLIER", "HIGH_RETENTION")

    # Verify Hook Breakdown
    assert report.hook_breakdown.score >= 20
    assert report.hook_breakdown.pattern_interrupt_present is True
    assert "Pattern Interrupt" in report.hook_breakdown.hook_type_detected

    # Verify Pacing & Dropoff curves
    assert len(report.scene_dropoffs) == 4
    assert report.scene_dropoffs[0].scene_number == 1
    assert report.scene_dropoffs[0].estimated_retention_pct >= 70.0

    # Verify 3 Optimized Hooks
    assert len(report.optimized_hooks) == 3
    for h in report.optimized_hooks:
        assert h.estimated_hook_score >= 25
        assert len(h.text) > 15

@pytest.mark.asyncio
async def test_retention_auditor_empty_script():
    auditor = RetentionAuditor()
    report = await auditor.audit_script(
        title="Empty",
        scenes=[],
        target_duration=30.0
    )
    assert report.overall_score == 0
    assert report.grade == "DROP_OFF_RISK"
    assert len(report.scene_dropoffs) == 0

def test_quick_retention_audit_endpoint():
    response = client.post(
        "/api/projects/retention/quick-audit",
        json={
            "topic": "Quantum Computing 2026",
            "narration": "Stop ignoring quantum encryption. If you store sensitive passwords today, hackers will decrypt them tomorrow. Comment below to safeguard your system.",
            "duration": 20.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "hook_breakdown" in data
    assert "optimized_hooks" in data
    assert len(data["optimized_hooks"]) == 3
    assert data["overall_score"] > 50

@pytest.mark.asyncio
async def test_project_retention_audit_and_hook_swap():
    app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    proj_id = uuid.uuid4()
    async with TestingSessionLocal() as session:
        project = Project(
            id=proj_id,
            topic="Next-Gen Cybersecurity",
            objective="Viral",
            audience="Engineers",
            duration=30,
            aspect_ratio="9:16",
            style="cinematic",
            status=ProjectStatus.APPROVED
        )
        session.add(project)

        script = Script(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Next-Gen Cybersecurity",
            hook="Original boring opening about computers.",
            body="Cyber attacks are happening.",
            cta="Follow for more."
        )
        session.add(script)

        scene1 = Scene(
            id=uuid.uuid4(),
            project_id=proj_id,
            script_id=script.id,
            scene_number=1,
            duration=3.5,
            narration="Original boring opening about computers.",
            visual_prompt="A computer on a desk"
        )
        scene2 = Scene(
            id=uuid.uuid4(),
            project_id=proj_id,
            script_id=script.id,
            scene_number=2,
            duration=4.0,
            narration="Cyber attacks are happening daily.",
            visual_prompt="Matrix code rain"
        )
        session.add(scene1)
        session.add(scene2)
        await session.commit()

    # 1. Test GET /retention-audit
    res_audit = client.get(f"/api/projects/{proj_id}/retention-audit")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert "overall_score" in audit_data
    assert len(audit_data["optimized_hooks"]) == 3

    # Pick the top optimized hook
    chosen_hook = audit_data["optimized_hooks"][0]["text"]

    # 2. Test POST /apply-optimized-hook
    res_apply = client.post(
        f"/api/projects/{proj_id}/apply-optimized-hook",
        json={"hook_text": chosen_hook}
    )
    assert res_apply.status_code == 200
    apply_data = res_apply.json()
    assert apply_data["status"] == "SUCCESS"
    assert apply_data["applied_hook"] == chosen_hook

    # 3. Verify in Database that Scene 1 was updated
    async with TestingSessionLocal() as session:
        updated_proj = await session.get(Project, proj_id)
        assert updated_proj is not None
        # Verify script hook
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Project).options(selectinload(Project.script), selectinload(Project.scenes)).where(Project.id == proj_id)
        r = await session.execute(stmt)
        p = r.scalar_one()
        assert p.script.hook == chosen_hook
        s1 = next(s for s in p.scenes if s.scene_number == 1)
        assert s1.narration == chosen_hook
