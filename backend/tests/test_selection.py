"""Tests for next-question selection.

The three tiers are the whole adaptive contract, and line coverage cannot
see them: every tier's query runs on every call, but only one of them
returns. These exercise each outcome directly.
"""

import random

import pytest
from sqlalchemy import select, update

from app import selection
from app.db.models import Attempt, Question, QuestionOption, Topic, User


def _question(difficulty_b: float, question_id: int = 0) -> Question:
    """Builds an unsaved question, for tests that need no database."""
    return Question(id=question_id, difficulty_b=difficulty_b)


class TestClosest:
    """Ranking and the randomesque pool, with no database involved."""

    def test_picks_the_nearest_when_only_one_candidate_exists(self):
        chosen = selection._closest(
            [_question(2.0)], theta=0.0, rng=random.Random(0)
        )
        assert chosen.difficulty_b == 2.0

    def test_only_considers_the_pool_size_nearest(self):
        """A far-off question cannot be chosen while nearer ones remain."""
        near = [_question(0.1 * i, i) for i in range(5)]
        far = _question(9.0, 99)
        for seed in range(50):
            chosen = selection._closest(
                near + [far], theta=0.0, rng=random.Random(seed)
            )
            assert chosen.id != 99

    def test_spreads_across_the_pool_rather_than_always_taking_nearest(self):
        candidates = [_question(float(i), i) for i in range(5)]
        picked = {
            selection._closest(
                candidates, theta=0.0, rng=random.Random(seed)
            ).id
            for seed in range(50)
        }
        assert len(picked) > 1

    def test_ranks_by_distance_not_by_signed_difference(self):
        """A question far below theta is as unwanted as one far above.

        Sorting on the raw difference would put b = -5 first, since it is
        the most negative, and drag it into the pool. Sorting on distance
        drops it.
        """
        far_below = _question(-5.0, 99)
        near_above = [_question(0.1 * i, i) for i in range(1, 6)]
        for seed in range(50):
            chosen = selection._closest(
                [far_below] + near_above, theta=0.0, rng=random.Random(seed)
            )
            assert chosen.id != 99


class TestTiers:
    """Which pool a question is drawn from, against the real schema."""

    @pytest.fixture
    async def student(self, session):
        user = User(display_name="Selector")
        session.add(user)
        await session.flush()
        return user.id

    @pytest.fixture
    async def logs(self, session):
        return await session.scalar(
            select(Topic.id).where(Topic.slug == "logarithms")
        )

    async def _answer(self, session, user_id, question, *, correct):
        """Records an attempt without going through the API."""
        option_id = await session.scalar(
            select(QuestionOption.id).where(
                QuestionOption.question_id == question.id,
                QuestionOption.is_correct.is_(correct),
            )
        )
        session.add(
            Attempt(
                user_id=user_id,
                question_id=question.id,
                topic_id=question.topic_id,
                selected_option_id=option_id,
                is_correct=correct,
                theta_before=0.0,
                theta_after=0.0,
                b_before=question.difficulty_b,
                b_after=question.difficulty_b,
                k_theta=0.3,
                k_b=0.3,
            )
        )
        await session.flush()

    async def test_serves_an_unseen_question_first(
        self, session, student, logs
    ):
        chosen = await selection.choose_question(
            session, user_id=student, topic_id=logs, theta=0.0
        )
        assert chosen is not None

    async def test_never_repeats_a_question_answered_correctly(
        self, session, student, logs
    ):
        seen = set()
        for _ in range(18):
            chosen = await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            assert chosen.id not in seen
            seen.add(chosen.id)
            await self._answer(session, student, chosen, correct=True)
        assert len(seen) == 18

    async def test_topic_completes_once_everything_is_answered_right(
        self, session, student, logs
    ):
        """The completion rule, which nothing else exercised."""
        for _ in range(18):
            chosen = await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            await self._answer(session, student, chosen, correct=True)

        assert (
            await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            is None
        )

    async def test_recycles_a_question_answered_wrong(
        self, session, student, logs
    ):
        """Tier two: exhaust the unseen pool, leaving one wrong answer."""
        wrong_id = None
        for i in range(18):
            chosen = await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            correct = i != 0
            if not correct:
                wrong_id = chosen.id
            await self._answer(session, student, chosen, correct=correct)

        again = await selection.choose_question(
            session, user_id=student, topic_id=logs, theta=0.0
        )
        assert again is not None
        assert again.id == wrong_id

    async def test_answering_it_right_retires_it_and_completes_the_topic(
        self, session, student, logs
    ):
        for i in range(18):
            chosen = await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            await self._answer(session, student, chosen, correct=i != 0)

        recycled = await selection.choose_question(
            session, user_id=student, topic_id=logs, theta=0.0
        )
        await self._answer(session, student, recycled, correct=True)

        assert (
            await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            is None
        )

    async def test_skips_retired_questions(self, session, student, logs):
        """An inactive question is never served, in either tier."""
        await session.execute(
            update(Question)
            .where(Question.topic_id == logs)
            .values(is_active=False)
        )
        await session.flush()

        assert (
            await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=0.0
            )
            is None
        )

    async def test_prefers_difficulty_near_the_students_ability(
        self, session, student, logs
    ):
        """A strong student is not handed the easiest questions."""
        chosen = [
            await selection.choose_question(
                session, user_id=student, topic_id=logs, theta=1.0
            )
            for _ in range(20)
        ]
        assert all(q.difficulty_b >= 0.0 for q in chosen)
