"""Chooses which question to serve next.

Two ideas drive this. Questions are ranked by how close their difficulty
sits to the student's ability, since a question they have an even chance
of answering tells you the most about them. Then one is picked at random
from the closest few rather than always taking the single nearest —
"randomesque" exposure control, which keeps the information high while
stopping one question being served to everyone.
"""

import random

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Attempt, Question

#: How many of the nearest candidates to choose between. Larger means more
#: variety and slightly less information per answer.
CANDIDATE_POOL_SIZE = 5


def _latest_attempt_ids(user_id: int, topic_id: int) -> Select:
    """Selects the id of each question's most recent attempt.

    Ordering by id rather than `answered_at` avoids ties: two answers can
    share a millisecond, but ids are strictly increasing.

    Args:
        user_id: Student to look at.
        topic_id: Topic to restrict to.

    Returns:
        A select yielding one attempt id per question.
    """
    return (
        select(func.max(Attempt.id))
        .where(Attempt.user_id == user_id, Attempt.topic_id == topic_id)
        .group_by(Attempt.question_id)
    )


def _unseen(user_id: int, topic_id: int) -> Select:
    """Selects active questions the student has never attempted."""
    attempted = select(Attempt.question_id).where(
        Attempt.user_id == user_id, Attempt.topic_id == topic_id
    )
    return select(Question).where(
        Question.topic_id == topic_id,
        Question.is_active.is_(True),
        Question.id.not_in(attempted),
    )


def _answered_wrong(user_id: int, topic_id: int) -> Select:
    """Selects active questions whose most recent attempt was wrong.

    Answering one correctly retires it from this tier, which is what makes
    "every question answered correctly at least once" the completion rule.
    """
    still_wrong = select(Attempt.question_id).where(
        Attempt.id.in_(_latest_attempt_ids(user_id, topic_id)),
        Attempt.is_correct.is_(False),
    )
    return select(Question).where(
        Question.topic_id == topic_id,
        Question.is_active.is_(True),
        Question.id.in_(still_wrong),
    )


def _closest(
    questions: list[Question],
    theta: float,
    rng: random.Random,
) -> Question:
    """Picks one of the questions nearest the student's ability.

    Args:
        questions: Candidates to choose from; must not be empty.
        theta: Student's current ability.
        rng: Source of randomness, injectable so tests can pin it.

    Returns:
        One question from the closest CANDIDATE_POOL_SIZE candidates.
    """
    ranked = sorted(questions, key=lambda q: abs(q.difficulty_b - theta))
    return rng.choice(ranked[:CANDIDATE_POOL_SIZE])


async def choose_question(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    theta: float,
    rng: random.Random | None = None,
) -> Question | None:
    """Chooses the next question for a student in one topic.

    Falls through three tiers: questions never attempted, then questions
    whose last attempt was wrong, then nothing — which means the student
    has answered every active question in the topic correctly.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        theta: Student's current ability in this topic.
        rng: Source of randomness, injectable so tests can pin it.

    Returns:
        The chosen question, or None when the topic is complete.
    """
    rng = rng or random.Random()
    for candidates in (
        _unseen(user_id, topic_id),
        _answered_wrong(user_id, topic_id),
    ):
        rows = list(await session.scalars(candidates))
        if rows:
            return _closest(rows, theta, rng)
    return None
