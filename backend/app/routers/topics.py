"""Listing the topics a student can be quizzed on."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.db.models import Question, Topic
from app.db.session import get_session

router = APIRouter(tags=["topics"])


@router.get("/topics", response_model=list[schemas.TopicOut])
async def list_topics(
    session: AsyncSession = Depends(get_session),
) -> list[schemas.TopicOut]:
    """Lists every topic, with how many active questions each holds.

    Without this there is no way for a client to discover the topicId
    that /next-question requires.

    Args:
        session: Injected database session.

    Returns:
        Every topic, ordered by slug.
    """
    rows = await session.execute(
        select(Topic, func.count(Question.id))
        .outerjoin(
            Question,
            (Question.topic_id == Topic.id) & Question.is_active.is_(True),
        )
        .group_by(Topic.id)
        .order_by(Topic.slug)
    )
    return [
        schemas.TopicOut(
            id=topic.id,
            slug=topic.slug,
            name=topic.name,
            description=topic.description,
            question_count=count,
        )
        for topic, count in rows
    ]
