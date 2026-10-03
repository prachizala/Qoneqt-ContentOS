import uuid
import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models.models import (
    Project, Script, Video, Publication, ProjectStatus, PublicationStatus
)
from integrations.qoneqt import QoneqtPublisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Publishing"])

@router.post("/{project_id}/publish", status_code=status.HTTP_200_OK)
async def publish_project_to_qoneqt(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Publishes an APPROVED project's rendered short-form video to the Qoneqt Global Feed.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.script),
            selectinload(Project.videos)
        )
        .where(Project.id == project_id)
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    if project.status != ProjectStatus.APPROVED and project.status != ProjectStatus.READY_FOR_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Project status is '{project.status.value}'. Must be APPROVED or READY_FOR_REVIEW before publishing."
        )

    if not project.videos:
        raise HTTPException(status_code=400, detail="No rendered video available for this project.")

    video = project.videos[-1]  # Select latest rendered video

    publisher = QoneqtPublisher()

    try:
        # Step 1: Upload media file
        upload_res = await publisher.upload_video(video.file_path)
        media_id = upload_res.get("media_id")

        # Step 2: Publish to global feed
        title = project.script.title if project.script else project.topic
        caption = project.script.hook if project.script else f"Short video on {project.topic}"
        tags = ["#Qoneqt", "#AIContent", f"#{project.topic.replace(' ', '')}"]

        publish_res = await publisher.publish_to_global_feed(
            title=title,
            caption=caption,
            media_id=media_id,
            tags=tags
        )

        # Step 3: Record publication in DB
        publication = Publication(
            id=uuid.uuid4(),
            project_id=project_id,
            platform="QONEQT",
            post_id=publish_res.get("post_id"),
            feed_url=publish_res.get("feed_url"),
            status=PublicationStatus.PUBLISHED,
            published_at=datetime.datetime.utcnow(),
            error_log=None
        )
        db.add(publication)

        # Update Project status to PUBLISHED
        project.status = ProjectStatus.PUBLISHED
        await db.commit()

        logger.info(f"Successfully published Project {project_id} to Qoneqt: {publish_res.get('feed_url')}")

        return {
            "message": "Video successfully published to Qoneqt Global Feed",
            "project_id": str(project_id),
            "status": project.status.value,
            "publication": {
                "id": str(publication.id),
                "platform": publication.platform,
                "post_id": publication.post_id,
                "feed_url": publication.feed_url,
                "published_at": publication.published_at.isoformat() if publication.published_at else None
            }
        }

    except Exception as exc:
        logger.error(f"Failed to publish Project {project_id} to Qoneqt: {exc}")

        # Log failed publication attempt in DB
        failed_pub = Publication(
            id=uuid.uuid4(),
            project_id=project_id,
            platform="QONEQT",
            status=PublicationStatus.FAILED,
            error_log=str(exc)
        )
        db.add(failed_pub)
        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Publication to Qoneqt failed: {exc}"
        )
