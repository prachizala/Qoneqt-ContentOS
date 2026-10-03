import uuid
import datetime
import enum
from typing import Optional, List, Any
from sqlalchemy import (
    String, Text, Integer, Float, DateTime, Enum as SQLEnum,
    ForeignKey, func, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base

# Dialect-agnostic JSON and UUID helpers
JSON_TYPE = JSON().with_variant(JSONB, "postgresql")
UUID_TYPE = PG_UUID(as_uuid=True)

class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RESEARCHING = "RESEARCHING"
    SCRIPTING = "SCRIPTING"
    GENERATING = "GENERATING"
    RENDERING = "RENDERING"
    QA_PENDING = "QA_PENDING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class SceneStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AssetType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    SUBTITLE = "SUBTITLE"

class VideoStatus(str, enum.Enum):
    RENDERING = "RENDERING"
    READY = "READY"
    FAILED = "FAILED"

class QASimpleStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"

class PublicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    CREATOR = "CREATOR"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class UserSubscription(Base):
    """
    Tracks persistent subscription state, quotas, billing cycles, and payment IDs.
    """
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(100), default="default_user", unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="FREE", nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    videos_limit: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    scripts_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    reset_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_provider: Mapped[Optional[str]] = mapped_column(String(50), default="RAZORPAY", nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    objective: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audience: Mapped[str] = mapped_column(String(100), default="general", nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="9:16", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    style: Mapped[str] = mapped_column(String(50), default="cinematic", nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_heartbeat: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    script: Mapped[Optional["Script"]] = relationship(
        "Script", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number"
    )
    assets: Mapped[List["Asset"]] = relationship(
        "Asset", back_populates="project", cascade="all, delete-orphan"
    )
    videos: Mapped[List["Video"]] = relationship(
        "Video", back_populates="project", cascade="all, delete-orphan"
    )
    qa_results: Mapped[List["QAResult"]] = relationship(
        "QAResult", back_populates="project", cascade="all, delete-orphan"
    )
    publications: Mapped[List["Publication"]] = relationship(
        "Publication", back_populates="project", cascade="all, delete-orphan"
    )

class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    raw_json: Mapped[Optional[Any]] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="script")
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="script", cascade="all, delete-orphan", order_by="Scene.scene_number"
    )

class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    visual_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    camera_direction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    kinetic_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    motion_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transition: Mapped[str] = mapped_column(String(50), default="fade", nullable=False)
    status: Mapped[SceneStatus] = mapped_column(
        SQLEnum(SceneStatus), default=SceneStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="scenes")
    script: Mapped["Script"] = relationship("Script", back_populates="scenes")
    assets: Mapped[List["Asset"]] = relationship(
        "Asset", back_populates="scene", cascade="all, delete-orphan"
    )

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID_TYPE, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    asset_type: Mapped[AssetType] = mapped_column(SQLEnum(AssetType), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    remote_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    local_path: Mapped[str] = mapped_column(String(512), nullable=False)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON_TYPE, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="assets")
    scene: Mapped[Optional["Scene"]] = relationship("Scene", back_populates="assets")

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    public_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    resolution: Mapped[str] = mapped_column(String(20), default="1080x1920", nullable=False)
    status: Mapped[VideoStatus] = mapped_column(
        SQLEnum(VideoStatus), default=VideoStatus.RENDERING, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="videos")

class QAResult(Base):
    __tablename__ = "qa_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technical_status: Mapped[QASimpleStatus] = mapped_column(SQLEnum(QASimpleStatus), nullable=False)
    content_status: Mapped[QASimpleStatus] = mapped_column(SQLEnum(QASimpleStatus), nullable=False)
    issues: Mapped[Optional[Any]] = mapped_column(JSON_TYPE, nullable=True)
    final_status: Mapped[QASimpleStatus] = mapped_column(SQLEnum(QASimpleStatus), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="qa_results")

class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(100), default="QONEQT", nullable=False)
    post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    feed_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[PublicationStatus] = mapped_column(
        SQLEnum(PublicationStatus), default=PublicationStatus.PENDING, nullable=False
    )
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="publications")
