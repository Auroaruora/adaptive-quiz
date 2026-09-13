"""End-to-end tests for the API.

The security-shaped tests matter most here: CLAUDE.md forbids sending the
correct answer or a question's difficulty to the frontend before an answer
is submitted, and that rule is only worth anything if something checks it.
"""

import pytest
from sqlalchemy import select

from app.db.models import Attempt, Question, QuestionOption


async def _answer(client, user_id, question_id, option_id):
    """Submits one answer and returns the parsed response."""
    response = await client.post(
        "/submit-answer",
        json={
            "userId": user_id,
            "questionId": question_id,
            "selectedOptionId": option_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _correct_option_id(session, question_id):
    return await session.scalar(
        select(QuestionOption.id).where(
            QuestionOption.question_id == question_id,
            QuestionOption.is_correct.is_(True),
        )
    )


async def _wrong_option_id(session, question_id):
    return await session.scalar(
        select(QuestionOption.id).where(
            QuestionOption.question_id == question_id,
            QuestionOption.is_correct.is_(False),
        )
    )


class TestCreateUser:
    """POST /users."""

    async def test_creates_a_student(self, client):
        response = await client.post(
            "/users", json={"displayName": "Ada"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["displayName"] == "Ada"
        assert body["id"] > 0
        assert "createdAt" in body

    async def test_rejects_an_empty_name(self, client):
        response = await client.post("/users", json={"displayName": ""})
        assert response.status_code == 422

    async def test_rejects_a_name_over_the_column_limit(self, client):
        response = await client.post(
            "/users", json={"displayName": "x" * 51}
        )
        assert response.status_code == 422


class TestNextQuestion:
    """GET /next-question."""

    async def test_serves_a_question_with_four_options(
        self, client, user_id, topic_id
    ):
        response = await client.get(
            f"/next-question?userId={user_id}&topicId={topic_id}"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["complete"] is False
        assert len(body["question"]["options"]) == 4

    async def test_reports_ability_as_a_number_and_a_band(
        self, client, user_id, topic_id
    ):
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        assert body["ability"]["theta"] == 0.0
        assert body["ability"]["level"] == "progressing"

    async def test_starts_at_a_question_of_middling_difficulty(
        self, client, user_id, topic_id, session
    ):
        """A new student sits at theta 0, so b = 0 items are nearest."""
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        difficulty = await session.scalar(
            select(Question.difficulty_b).where(
                Question.id == body["question"]["id"]
            )
        )
        assert difficulty == pytest.approx(0.0)

    async def test_unknown_user_is_not_found(self, client, topic_id):
        response = await client.get(
            f"/next-question?userId=99999999&topicId={topic_id}"
        )
        assert response.status_code == 404

    async def test_unknown_topic_is_not_found(self, client, user_id):
        response = await client.get(
            f"/next-question?userId={user_id}&topicId=99999999"
        )
        assert response.status_code == 404

    async def test_rejects_a_non_positive_id(self, client, topic_id):
        response = await client.get(
            f"/next-question?userId=0&topicId={topic_id}"
        )
        assert response.status_code == 422


class TestAnswerSecrecy:
    """The rule from CLAUDE.md, enforced rather than assumed."""

    async def test_a_served_question_hides_everything_revealing(
        self, client, user_id, topic_id
    ):
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        question = body["question"]

        assert "difficultyB" not in question
        assert "difficulty_b" not in question
        for option in question["options"]:
            assert set(option) == {"id", "text", "position"}

    async def test_no_revealing_word_appears_anywhere_in_the_payload(
        self, client, user_id, topic_id
    ):
        """Guards against a future field leaking by a different name."""
        raw = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).text.lower()
        for forbidden in (
            "iscorrect",
            "is_correct",
            "correct_flag",
            "misconception",
            "solution",
            "difficulty",
        ):
            assert forbidden not in raw


class TestSubmitAnswer:
    """POST /submit-answer."""

    async def test_a_correct_answer_raises_ability(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _correct_option_id(session, served["id"])

        body = await _answer(client, user_id, served["id"], option)
        feedback = body["feedback"]

        assert feedback["isCorrect"] is True
        assert feedback["thetaAfter"] > feedback["thetaBefore"]
        assert feedback["misconception"] is None
        assert len(feedback["solution"]) >= 2

    async def test_a_wrong_answer_explains_the_specific_mistake(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _wrong_option_id(session, served["id"])

        feedback = (
            await _answer(client, user_id, served["id"], option)
        )["feedback"]

        assert feedback["isCorrect"] is False
        assert feedback["thetaAfter"] < feedback["thetaBefore"]
        assert feedback["misconception"]
        assert feedback["correctOptionId"] != option

    async def test_persists_an_attempt_that_can_be_replayed(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _correct_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        attempt = await session.scalar(
            select(Attempt).where(Attempt.user_id == user_id)
        )
        assert attempt is not None
        assert attempt.k_theta > 0
        assert attempt.k_b > 0
        assert attempt.theta_after != attempt.theta_before
        assert attempt.b_after != attempt.b_before

    async def test_updates_the_question_counters(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _correct_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        question = await session.get(Question, served["id"])
        await session.refresh(question)
        assert question.times_answered == 1
        assert question.times_correct == 1

    async def test_never_serves_the_same_question_twice_running(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _correct_option_id(session, served["id"])

        body = await _answer(client, user_id, served["id"], option)
        assert body["next"]["question"]["id"] != served["id"]

    async def test_rejects_an_option_from_another_question(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        other = await session.scalar(
            select(QuestionOption.id).where(
                QuestionOption.question_id != served["id"]
            )
        )
        response = await client.post(
            "/submit-answer",
            json={
                "userId": user_id,
                "questionId": served["id"],
                "selectedOptionId": other,
            },
        )
        assert response.status_code == 400

    async def test_unknown_question_is_not_found(self, client, user_id):
        response = await client.post(
            "/submit-answer",
            json={
                "userId": user_id,
                "questionId": 99999999,
                "selectedOptionId": 1,
            },
        )
        assert response.status_code == 404


class TestProgress:
    """GET /progress/{user_id}."""

    async def test_reports_every_topic_including_untouched_ones(
        self, client, user_id
    ):
        body = (await client.get(f"/progress/{user_id}")).json()
        slugs = {t["slug"] for t in body["topics"]}
        assert slugs == {"derivatives", "logarithms", "trigonometry"}

    async def test_an_untouched_topic_starts_empty(self, client, user_id):
        body = (await client.get(f"/progress/{user_id}")).json()
        topic = body["topics"][0]
        assert topic["series"] == []
        assert topic["summary"]["answered"] == 0
        assert topic["summary"]["theta"] == 0.0
        assert topic["summary"]["total"] == 18

    async def test_an_answer_appears_in_the_series(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _correct_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(
            t for t in body["topics"] if t["slug"] == "logarithms"
        )
        assert logs["summary"]["answered"] == 1
        assert logs["summary"]["correct"] == 1
        assert logs["summary"]["mastered"] == 1
        assert len(logs["series"]) == 1
        assert logs["series"][0]["isCorrect"] is True

    async def test_a_wrong_answer_is_not_counted_as_mastered(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _wrong_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(
            t for t in body["topics"] if t["slug"] == "logarithms"
        )
        assert logs["summary"]["answered"] == 1
        assert logs["summary"]["correct"] == 0
        assert logs["summary"]["mastered"] == 0

    async def test_unknown_user_is_not_found(self, client):
        response = await client.get("/progress/99999999")
        assert response.status_code == 404
