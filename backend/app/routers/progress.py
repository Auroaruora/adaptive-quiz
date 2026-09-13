"""Reporting a student's history, for the dashboard."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import irt, schemas, services
from app.db.models import Attempt, Question, Topic, User, UserTopicAbility
from app.db.session import get_session

router = APIRouter(tags=["progress"])


@router.get("/progress/{user_id}", response_model=schemas.ProgressOut)
async def progress(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> schemas.ProgressOut:
    """Returns per-topic ability history for one student.

    Every topic is reported, including untouched ones, so the dashboard
    can show a complete picture rather than topics appearing only once
    they have been started.

    Args:
        user_id: Student to report on.
        session: Injected database session.

    Returns:
        A summary and full answer series for each topic.

    Raises:
        HTTPException: 404 when the student does not exist.
    """
    if await session.get(User, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user {user_id} does not exist",
        )

    topics = []
    for topic in await session.scalars(select(Topic).order_by(Topic.slug)):
        ability = await session.get(UserTopicAbility, (user_id, topic.id))
        theta = ability.theta if ability else 0.0

        attempts = await session.scalars(
            select(Attempt)
            .where(Attempt.user_id == user_id, Attempt.topic_id == topic.id)
            .order_by(Attempt.id)
        )
        series = [
            schemas.SeriesPoint(
                at=a.answered_at, theta=a.theta_after, is_correct=a.is_correct
            )
            for a in attempts
        ]

        total = await session.scalar(
            select(func.count())
            .select_from(Question)
            .where(
                Question.topic_id == topic.id,
                Question.is_active.is_(True),
            )
        )

        topics.append(
            schemas.TopicProgress(
                slug=topic.slug,
                name=topic.name,
                summary=schemas.TopicSummary(
                    theta=theta,
                    level=irt.ability_level(theta),
                    answered=len(series),
                    correct=sum(p.is_correct for p in series),
                    mastered=await services.mastered_count(
                        session, user_id=user_id, topic_id=topic.id
                    ),
                    total=total,
                ),
                series=series,
            )
        )

    return schemas.ProgressOut(user_id=user_id, topics=topics)
