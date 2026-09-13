"""Database reads and writes shared between endpoints.

Keeps the routers thin, and keeps the rule that answer-revealing data
never reaches a question being asked in one place rather than repeated at
every call site.
"""

import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import irt, schemas, selection
from app.db.models import (
    Attempt,
    Question,
    QuestionOption,
    QuestionStep,
    Topic,
    UserTopicAbility,
)


async def get_or_create_ability(
    session: AsyncSession, *, user_id: int, topic_id: int
) -> UserTopicAbility:
    """Fetches a student's ability in a topic, creating it if absent.

    Rows are created lazily on first contact rather than seeded for every
    topic when a user is created.

    Args:
        session: Open async session.
        user_id: Student.
        topic_id: Topic.

    Returns:
        The ability row, starting at theta 0.0 when newly created.
    """
    ability = await session.get(UserTopicAbility, (user_id, topic_id))
    if ability is None:
        ability = UserTopicAbility(
            user_id=user_id, topic_id=topic_id, theta=0.0, attempts_count=0
        )
        session.add(ability)
        await session.flush()
    return ability


async def question_payload(
    session: AsyncSession, question: Question
) -> schemas.QuestionOut:
    """Builds the public view of a question.

    Selects only the columns a student may see before answering, so the
    correct option, its misconception, the worked solution and
    difficulty_b cannot leak through this path.

    Args:
        session: Open async session.
        question: Question to render.

    Returns:
        The question as the frontend will receive it.
    """
    slug = await session.scalar(
        select(Topic.slug).where(Topic.id == question.topic_id)
    )
    options = await session.scalars(
        select(QuestionOption)
        .where(QuestionOption.question_id == question.id)
        .order_by(QuestionOption.position)
    )
    return schemas.QuestionOut(
        id=question.id,
        topic_slug=slug,
        stem=question.stem,
        options=[
            schemas.OptionOut(id=o.id, text=o.option_text, position=o.position)
            for o in options
        ],
    )


async def next_question_payload(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    theta: float,
    rng: random.Random | None = None,
) -> schemas.NextQuestionOut:
    """Chooses the next question and wraps it with the current ability.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        theta: Student's current ability in this topic.
        rng: Source of randomness, injectable so tests can pin it.

    Returns:
        The next question, or a completion signal when none is left.
    """
    question = await selection.choose_question(
        session, user_id=user_id, topic_id=topic_id, theta=theta, rng=rng
    )
    return schemas.NextQuestionOut(
        question=(
            await question_payload(session, question) if question else None
        ),
        ability=schemas.AbilityOut(theta=theta, level=irt.ability_level(theta)),
        complete=question is None,
    )


async def solution_steps(session: AsyncSession, question_id: int) -> list[str]:
    """Returns a question's worked solution in order.

    Args:
        session: Open async session.
        question_id: Question whose solution is wanted.

    Returns:
        The steps, ordered from first to last.
    """
    rows = await session.scalars(
        select(QuestionStep.body)
        .where(QuestionStep.question_id == question_id)
        .order_by(QuestionStep.step_number)
    )
    return list(rows)


async def mastered_count(
    session: AsyncSession, *, user_id: int, topic_id: int
) -> int:
    """Counts questions whose most recent answer was correct.

    This is the same rule that decides when a topic is complete, so the
    dashboard and the selector never disagree about progress.

    Args:
        session: Open async session.
        user_id: Student.
        topic_id: Topic.

    Returns:
        Number of questions currently mastered.
    """
    latest = (
        select(func.max(Attempt.id))
        .where(Attempt.user_id == user_id, Attempt.topic_id == topic_id)
        .group_by(Attempt.question_id)
    )
    return await session.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.id.in_(latest), Attempt.is_correct.is_(True))
    )
