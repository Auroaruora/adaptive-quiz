"""Database reads and writes shared between endpoints.

Keeps the routers thin, and keeps the rule that answer-revealing data
never reaches a question being asked in one place rather than repeated at
every call site.
"""

import datetime
import random
from collections.abc import Collection, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import irt, practice, schemas, selection
from app.db.models import (
    Attempt,
    Question,
    QuestionOption,
    QuestionStep,
    QuestionTag,
    Tag,
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
        tags=await question_tags(session, question),
        options=[
            schemas.OptionOut(id=o.id, text=o.option_text, position=o.position)
            for o in options
        ],
    )


async def question_tags(
    session: AsyncSession, question: Question
) -> list[schemas.TagOut]:
    """A question's tags, most specific first.

    Specific means rare within the topic. Sorting here rather than in the
    client keeps the usage counts on the side that already has them.

    Args:
        session: Open async session.
        question: Question whose tags are wanted.

    Returns:
        The tags, rarest first.
    """
    usage = (
        select(QuestionTag.tag_id, func.count().label("uses"))
        .join(Question, Question.id == QuestionTag.question_id)
        .where(
            Question.topic_id == question.topic_id,
            Question.is_active.is_(True),
        )
        .group_by(QuestionTag.tag_id)
        .subquery()
    )
    rows = await session.execute(
        select(Tag.slug, Tag.name)
        .join(QuestionTag, QuestionTag.tag_id == Tag.id)
        .join(usage, usage.c.tag_id == Tag.id)
        .where(QuestionTag.question_id == question.id)
        .order_by(usage.c.uses, Tag.slug)
    )
    return [schemas.TagOut(slug=slug, name=name) for slug, name in rows]


async def next_question_payload(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    theta: float,
    rng: random.Random | None = None,
    tag_slugs: Sequence[str] | None = None,
    exclude: Collection[int] = (),
) -> schemas.NextQuestionOut:
    """Chooses the next question and wraps it with the current ability.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        theta: Student's current ability in this topic.
        rng: Source of randomness, injectable so tests can pin it.
        tag_slugs: Restricts the pool to questions carrying any of these.
        exclude: Question ids already served this session.

    Returns:
        The next question, or a completion signal when none is left.
    """
    question = await selection.choose_question(
        session,
        user_id=user_id,
        topic_id=topic_id,
        theta=theta,
        rng=rng,
        tag_slugs=tag_slugs,
        exclude=exclude,
    )
    remaining = await selection.count_available(
        session,
        user_id=user_id,
        topic_id=topic_id,
        tag_slugs=tag_slugs,
        exclude=exclude,
    )
    return schemas.NextQuestionOut(
        question=(
            await question_payload(session, question) if question else None
        ),
        ability=schemas.AbilityOut(theta=theta, level=irt.ability_level(theta)),
        complete=question is None,
        remaining=remaining,
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


async def latest_outcomes(
    session: AsyncSession, *, user_id: int, topic_id: int
) -> dict[int, bool]:
    """Whether each attempted question was last answered correctly.

    "Last answered correctly" is the rule that decides when a topic is
    complete, so everything derived from this — mastered, wrong, and the
    per-concept rings — agrees with the selector about progress.

    Args:
        session: Open async session.
        user_id: Student.
        topic_id: Topic.

    Returns:
        Question id to the outcome of its most recent attempt. Questions
        never attempted are absent.
    """
    latest = (
        select(func.max(Attempt.id))
        .where(Attempt.user_id == user_id, Attempt.topic_id == topic_id)
        .group_by(Attempt.question_id)
    )
    rows = await session.execute(
        select(Attempt.question_id, Attempt.is_correct).where(
            Attempt.id.in_(latest)
        )
    )
    return {question_id: bool(is_correct) for question_id, is_correct in rows}


async def _questions_by_tag(
    session: AsyncSession, *, topic_id: int
) -> dict[str, set[int]]:
    """Every active question in a topic, grouped by tag slug."""
    rows = await session.execute(
        select(Tag.slug, QuestionTag.question_id)
        .join(QuestionTag, QuestionTag.tag_id == Tag.id)
        .join(Question, Question.id == QuestionTag.question_id)
        .where(Question.topic_id == topic_id, Question.is_active.is_(True))
    )
    grouped: dict[str, set[int]] = {}
    for slug, question_id in rows:
        grouped.setdefault(slug, set()).add(question_id)
    return grouped


async def weak_spots(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    now: datetime.datetime | None = None,
    limit: int = 3,
) -> list[schemas.WeakSpot]:
    """The tags a student is currently getting wrong, worst first.

    Ordered by the same decayed urgency that steers selection, so the
    dashboard names the things the quiz is about to serve rather than a
    separate opinion about them. Alongside each is where that concept's
    questions stand — last answered right, last answered wrong, or not yet
    practised — counted in questions so the parts add up to the whole.

    Args:
        session: Open async session.
        user_id: Student.
        topic_id: Topic.
        now: Current time, injectable so tests can age mistakes.
        limit: How many to return.

    Returns:
        Up to `limit` weak spots, or an empty list when nothing has been
        answered incorrectly.
    """
    now = now or datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    rows = await session.execute(
        select(Tag.slug, Tag.name, Attempt.answered_at)
        .join(QuestionTag, QuestionTag.tag_id == Tag.id)
        .join(Attempt, Attempt.question_id == QuestionTag.question_id)
        .where(
            Attempt.user_id == user_id,
            Attempt.topic_id == topic_id,
            Attempt.is_correct.is_(False),
        )
    )

    misses: dict[str, tuple[str, list[datetime.datetime]]] = {}
    for slug, name, answered_at in rows:
        misses.setdefault(slug, (name, []))[1].append(answered_at)

    ranked = sorted(
        misses.items(),
        key=lambda item: practice.urgency(item[1][1], now),
        reverse=True,
    )
    if not ranked:
        return []

    outcomes = await latest_outcomes(
        session, user_id=user_id, topic_id=topic_id
    )
    by_tag = await _questions_by_tag(session, topic_id=topic_id)
    spots = []
    for slug, (name, _) in ranked[:limit]:
        questions = by_tag.get(slug, set())
        states = [outcomes[q] for q in questions if q in outcomes]
        spots.append(
            schemas.WeakSpot(
                slug=slug,
                name=name,
                total=len(questions),
                correct=sum(states),
                wrong=len(states) - sum(states),
            )
        )
    return spots
