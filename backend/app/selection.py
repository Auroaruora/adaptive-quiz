"""Chooses which question to serve next.

New questions are ranked by how well they answer what the student keeps
getting wrong. Each mistake contributes its tags to a weakness profile,
and a question scores by how much it overlaps with that — so missing the
product rule brings more product-rule questions, not whatever happens to
sit nearby on the difficulty scale. Difficulty breaks ties, and one is
picked from the closest few rather than always the single best, so no two
students walk the same path.

A student with no mistakes has an empty profile and scores zero
everywhere, which collapses the whole thing to ranking by difficulty. The
first question of a session needs no special case.

Once the new questions run out, the pool becomes what they last got
wrong, and time takes over: a question just seen is held back, and a
mistake pulls less the older it gets. That half lives in `practice`;
similarity lives in `tags`.
"""

import collections
import datetime
import random
from collections.abc import Collection, Mapping, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import practice, tags
from app.db.models import Attempt, Question, QuestionTag, Tag

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


def _tagged(tag_slugs: Sequence[str]) -> Select:
    """Selects the ids of questions carrying any of the tags."""
    return (
        select(QuestionTag.question_id)
        .join(Tag, Tag.id == QuestionTag.tag_id)
        .where(Tag.slug.in_(tag_slugs))
    )


def _narrowed(
    query: Select,
    tag_slugs: Sequence[str] | None,
    exclude: Collection[int],
) -> Select:
    """Applies the concept filter and the session's exclusions to a tier.

    Both tiers narrow the same way, so a question excluded from the unseen
    tier cannot slip back in through the answered-wrong one.
    """
    if tag_slugs:
        query = query.where(Question.id.in_(_tagged(tag_slugs)))
    if exclude:
        query = query.where(Question.id.not_in(list(exclude)))
    return query


def _unseen(
    user_id: int,
    topic_id: int,
    tag_slugs: Sequence[str] | None = None,
    exclude: Collection[int] = (),
) -> Select:
    """Selects active questions the student has never attempted."""
    attempted = select(Attempt.question_id).where(
        Attempt.user_id == user_id, Attempt.topic_id == topic_id
    )
    query = select(Question).where(
        Question.topic_id == topic_id,
        Question.is_active.is_(True),
        Question.id.not_in(attempted),
    )
    return _narrowed(query, tag_slugs, exclude)


def _answered_wrong(
    user_id: int,
    topic_id: int,
    tag_slugs: Sequence[str] | None = None,
    exclude: Collection[int] = (),
) -> Select:
    """Selects active questions whose most recent attempt was wrong.

    Answering one correctly retires it from this tier, which is what makes
    "every question answered correctly at least once" the completion rule.
    """
    still_wrong = select(Attempt.question_id).where(
        Attempt.id.in_(_latest_attempt_ids(user_id, topic_id)),
        Attempt.is_correct.is_(False),
    )
    query = select(Question).where(
        Question.topic_id == topic_id,
        Question.is_active.is_(True),
        Question.id.in_(still_wrong),
    )
    return _narrowed(query, tag_slugs, exclude)


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


async def _tags_by_question(
    session: AsyncSession, *, topic_id: int
) -> dict[int, frozenset[str]]:
    """Every active question's tags, for one topic."""
    rows = await session.execute(
        select(Question.id, Tag.slug)
        .join(QuestionTag, QuestionTag.question_id == Question.id)
        .join(Tag, Tag.id == QuestionTag.tag_id)
        .where(Question.topic_id == topic_id, Question.is_active.is_(True))
    )
    grouped: dict[int, set[str]] = {}
    for question_id, slug in rows:
        grouped.setdefault(question_id, set()).add(slug)
    return {qid: frozenset(slugs) for qid, slugs in grouped.items()}


def _steered(
    questions: list[Question],
    question_tags: Mapping[int, frozenset[str]],
    mistakes: Mapping[int, list[datetime.datetime]],
    now: datetime.datetime,
    theta: float,
    rng: random.Random,
) -> Question:
    """Picks a new question, leaning toward what the student keeps missing.

    Ranking is by how well a question answers the student's mistakes,
    with difficulty breaking ties. A student with no mistakes gets an
    affinity of zero for everything, so this collapses to ranking by
    difficulty with no special case for the first question of a session.
    """
    usage = collections.Counter(
        tag for one_question in question_tags.values() for tag in one_question
    )
    weights = tags.tag_weights(usage, len(question_tags) or 1)
    profile = tags.weakness(
        (question_tags.get(qid, frozenset()), practice.urgency(when, now))
        for qid, when in mistakes.items()
    )

    ranked = sorted(
        questions,
        key=lambda q: (
            -tags.affinity(
                question_tags.get(q.id, frozenset()), profile, weights
            ),
            abs(q.difficulty_b - theta),
        ),
    )
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


async def count_available(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    tag_slugs: Sequence[str] | None = None,
    exclude: Collection[int] = (),
) -> int:
    """Counts the questions either tier could still serve.

    A session sizes its run from this on its first question, so a concept
    with two questions shows a two-segment bar rather than ten.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        tag_slugs: The same narrowing `choose_question` applies.
        exclude: The same exclusions `choose_question` applies.

    Returns:
        Unseen plus last-answered-wrong, after narrowing.
    """
    total = 0
    for tier in (_unseen, _answered_wrong):
        query = tier(user_id, topic_id, tag_slugs, exclude)
        total += await session.scalar(
            select(func.count()).select_from(query.subquery())
        )
    return total


async def choose_question(
    session: AsyncSession,
    *,
    user_id: int,
    topic_id: int,
    theta: float,
    rng: random.Random | None = None,
    now: datetime.datetime | None = None,
    tag_slugs: Sequence[str] | None = None,
    exclude: Collection[int] = (),
) -> Question | None:
    """Chooses the next question for a student in one topic.

    Unseen questions come first, steered toward the tags the student has
    been getting wrong. Once those run out, the pool is the questions they
    last got wrong, and two things about time take over: a question just
    seen is held back, and older mistakes pull less than recent ones.

    Args:
        session: Open async session.
        user_id: Student to serve.
        topic_id: Topic to serve from.
        theta: Student's current ability in this topic.
        rng: Source of randomness, injectable so tests can pin it.
        now: Current time, injectable so tests can age mistakes.
        tag_slugs: Restricts the pool to questions carrying any of these
            concepts, for practising weak spots. None or empty serves the
            whole topic.
        exclude: Question ids never to serve, however the tiers fall.
            A session passes what it has already asked, so nothing repeats
            within one sitting.

    Returns:
        The chosen question, or None when nothing is left after the
        narrowing: the whole topic, one concept, or one session's pool.
    """
    rng = rng or random.Random()
    now = now or datetime.datetime.now(datetime.UTC).replace(tzinfo=None)

    mistakes = await _mistake_times(session, user_id=user_id, topic_id=topic_id)

    unseen = list(
        await session.scalars(_unseen(user_id, topic_id, tag_slugs, exclude))
    )
    if unseen:
        return _steered(
            unseen,
            await _tags_by_question(session, topic_id=topic_id),
            mistakes,
            now,
            theta,
            rng,
        )

    wrong = list(
        await session.scalars(
            _answered_wrong(user_id, topic_id, tag_slugs, exclude)
        )
    )
    if not wrong:
        return None

    recent = await _recently_seen(session, user_id=user_id, topic_id=topic_id)
    spaced = [q for q in wrong if q.id not in recent]

    # Falling back to the recently seen rather than returning None: a
    # student with two questions left should still get one, even if both
    # are fresh in mind.
    return _most_urgent(spaced or wrong, mistakes, now, rng)
