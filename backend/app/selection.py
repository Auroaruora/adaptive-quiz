"""Chooses which question to serve next.

New questions are ranked by how close their difficulty sits to the
student's ability, since a question they have an even chance of answering
tells you the most about them. One is then picked at random from the
closest few rather than always the single nearest — "randomesque"
exposure control, so no two students walk the same path.

Once the new questions run out the rule changes, because what a student
keeps getting wrong matters more than what is well matched. Time drives
that half: a question just seen is held back, and a mistake pulls less
the older it gets. Both live in `practice`.
"""

import datetime
import random

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import practice
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


async def _recently_seen(
    session: AsyncSession, *, user_id: int, topic_id: int
) -> set[int]:
    """Questions answered within the last few attempts."""
    rows = await session.scalars(
        select(Attempt.question_id)
        .where(Attempt.user_id == user_id, Attempt.topic_id == topic_id)
        .order_by(Attempt.id.desc())
        .limit(practice.SPACING_WINDOW)
    )
    return set(rows)


async def _mistake_times(
    session: AsyncSession, *, user_id: int, topic_id: int
) -> dict[int, list[datetime.datetime]]:
    """When each question was answered incorrectly, per question."""
    rows = await session.execute(
        select(Attempt.question_id, Attempt.answered_at).where(
            Attempt.user_id == user_id,
            Attempt.topic_id == topic_id,
            Attempt.is_correct.is_(False),
        )
    )
    times: dict[int, list[datetime.datetime]] = {}
    for question_id, answered_at in rows:
        times.setdefault(question_id, []).append(answered_at)
    return times


def _most_urgent(
    questions: list[Question],
    mistakes: dict[int, list[datetime.datetime]],
    now: datetime.datetime,
    rng: random.Random,
) -> Question:
    """Picks among the questions whose mistakes weigh heaviest.

    Weighted rather than ranked-then-uniform. Taking the top few by
    urgency and choosing evenly between them would throw the decay away
    exactly when it matters: with three questions left, a mistake from
    January would be as likely as one from this morning. Weighting by
    urgency keeps recent mistakes dominant while still letting an older
    one resurface occasionally, which is the review you want anyway.

    Callers pass only questions whose most recent attempt was wrong, so
    every one has at least one mistake and no weight is zero. That is an
    invariant rather than something checked: if it were ever broken,
    `random.choices` raising is a better outcome than silently serving
    the wrong thing.
    """
    weights = [practice.urgency(mistakes[q.id], now) for q in questions]
    return rng.choices(questions, weights=weights, k=1)[0]


async def choose_question(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    theta: float,
    rng: random.Random | None = None,
    now: datetime.datetime | None = None,
) -> Question | None:
    """Chooses the next question for a student in one topic.

    Unseen questions come first, chosen for how well they match the
    student's ability. Once those run out, the pool is the questions they
    last got wrong, and two things about time take over: a question just
    seen is held back, and older mistakes pull less than recent ones.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        theta: Student's current ability in this topic.
        rng: Source of randomness, injectable so tests can pin it.
        now: Current time, injectable so tests can age mistakes.

    Returns:
        The chosen question, or None when the topic is complete.
    """
    rng = rng or random.Random()
    now = now or datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    unseen = list(await session.scalars(_unseen(user_id, topic_id)))
    if unseen:
        return _closest(unseen, theta, rng)

    wrong = list(await session.scalars(_answered_wrong(user_id, topic_id)))
    if not wrong:
        return None

    recent = await _recently_seen(session, user_id=user_id, topic_id=topic_id)
    spaced = [q for q in wrong if q.id not in recent]

    # Falling back to the recently seen rather than returning None: a
    # student with two questions left should still get one, even if both
    # are fresh in mind.
    return _most_urgent(
        spaced or wrong,
        await _mistake_times(session, user_id=user_id, topic_id=topic_id),
        now,
        rng,
    )
