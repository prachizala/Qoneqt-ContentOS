from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.models import (
    ProjectStatus,
    SceneStatus,
    VideoStatus,
    QASimpleStatus,
    PublicationStatus,
)

class ContentRequestCreate(BaseModel):
    """
    Pydantic schema for validating incoming topic / video content generation requests.
    """
    topic: str = Field(..., min_length=1, description="Core topic or headline for video generation.")
    objective: Optional[str] = Field(default=None, description="Optional strategic objective or tone target.")
    tone: Optional[str] = Field(default=None, description="Target tone and hook style (e.g. Viral / Hook Driven, Informative & Educational, Engaging Storytelling, Satirical / Humorous).")
    hookStyle: Optional[str] = Field(default=None, description="Alias for tone / hook style.")
    audience: str = Field(default="general", description="Target audience segment.")
    duration: int = Field(default=30, ge=10, le=180, description="Target video duration in seconds (10-180).")
    aspect_ratio: str = Field(default="9:16", description="Video canvas aspect ratio (9:16 for short-form reels).")
    language: str = Field(default="en", description="Primary narration and caption language code.")
    style: str = Field(default="cinematic", description="Visual and narrative aesthetic style.")
    visualStyle: Optional[str] = Field(default=None, description="Alias for visual style.")

class ContentRequestResponse(BaseModel):
    """
    Pydantic schema for returning project metadata.
    """
    id: UUID
    topic: str
    objective: Optional[str] = None
    audience: str
    duration: int
    aspect_ratio: str
    language: str
    style: str
    status: ProjectStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScriptResponse(BaseModel):
    """
    Pydantic schema for generated AI script details.
    """
    id: UUID
    project_id: UUID
    title: str
    hook: str
    body: str
    cta: str
    hook_variations: Optional[Dict[str, str]] = None
    raw_json: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SceneResponse(BaseModel):
    """
    Pydantic schema for individual storyboard scene plans.
    """
    id: UUID
    project_id: UUID
    script_id: UUID
    scene_number: int
    duration: float
    narration: str
    visual_prompt: str
    camera_direction: Optional[str] = None
    kinetic_text: Optional[str] = None
    motion_prompt: Optional[str] = None
    caption: Optional[str] = None
    transition: str
    status: SceneStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VideoResponse(BaseModel):
    """
    Pydantic schema for assembled video artifact details.
    """
    id: UUID
    project_id: UUID
    file_path: str
    public_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration: float
    resolution: str
    status: VideoStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QAResultResponse(BaseModel):
    """
    Pydantic schema for quality assurance validation results.
    """
    id: UUID
    project_id: UUID
    technical_status: QASimpleStatus
    content_status: QASimpleStatus
    issues: Optional[List[Any]] = None
    final_status: QASimpleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PublicationResponse(BaseModel):
    """
    Pydantic schema for Qoneqt platform publishing records.
    """
    id: UUID
    project_id: UUID
    platform: str
    post_id: Optional[str] = None
    feed_url: Optional[str] = None
    status: PublicationStatus
    published_at: Optional[datetime] = None
    error_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectDetailResponse(ContentRequestResponse):
    """
    Comprehensive Pydantic schema including nested script, scenes, QA results, and videos.
    """
    script: Optional[ScriptResponse] = None
    scenes: List[SceneResponse] = []
    qa_results: List[QAResultResponse] = []
    videos: List[VideoResponse] = []
    publications: List[PublicationResponse] = []

    model_config = ConfigDict(from_attributes=True)
