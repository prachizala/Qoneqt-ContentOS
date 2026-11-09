import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.app.database import Base, get_db
from backend.main import app

# Create in-memory SQLite engine for local API route testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
from sqlalchemy.pool import StaticPool
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)
from backend.app.models.models import Project, Script, Scene, Asset, Video, QAResult, Publication  # noqa: F401
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE projects ADD COLUMN last_heartbeat DATETIME"))
        except Exception:
            pass
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "qoneqt-ai-content-factory-backend"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "documentation" in data

def test_list_projects_empty():
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_subscription_usage():
    response = client.get("/api/subscription/usage")
    assert response.status_code == 200
    data = response.json()
    assert "tier_id" in data
    assert "monthly_videos_limit" in data

def test_create_order():
    response = client.post(
        "/api/subscription/create-order",
        json={"plan": "creator", "amount": 499, "currency": "INR"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "order_id" in data
    assert data["amount"] == 49900
    assert data["currency"] == "INR"

def test_capture_payment_and_db_quota():
    response = client.post(
        "/api/subscription/capture-payment",
        json={
            "plan": "creator",
            "amount": 499,
            "order_id": "order_test_123",
            "payment_id": "pay_test_456",
            "card_number": "4532015112830366",
            "expiry": "12 / 28",
            "cvv": "123",
            "name_on_card": "Prachi Zala"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["subscription"]["plan"] == "CREATOR"
    assert data["subscription"]["monthly_videos_limit"] == 15
    assert data["subscription"]["monthly_scripts_limit"] == 100
    assert data["subscription"]["subscription_status"] == "ACTIVE"

def test_subscription_webhook():
    response = client.post(
        "/api/subscription/webhook",
        json={
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_wh_test_789",
                        "order_id": "order_wh_test_789",
                        "notes": {"plan": "CREATOR"}
                    }
                }
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["processed"] is True

from unittest.mock import patch

def test_generate_pipeline_endpoint():
    with patch("backend.app.routers.projects.run_pipeline") as mock_run:
        response = client.post(
            "/api/generate-pipeline",
        json={
            "topic": "Future of Autonomous AI Robotics 2026",
            "audience": "general",
            "duration": 30,
            "aspect_ratio": "9:16",
            "style": "cinematic"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["topic"] == "Future of Autonomous AI Robotics 2026"


