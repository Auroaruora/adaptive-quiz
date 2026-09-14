"""End-to-end tests for the API.

The security-shaped tests matter most here: CLAUDE.md forbids sending the
correct answer or a question's difficulty to the frontend before an answer
is submitted, and that rule is only worth anything if something checks it.
"""

from sqlalchemy import func, select, update

from app import selection
from app.db.models import Attempt, Question, QuestionOption, QuestionTag, Tag


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
        response = await client.post("/users", json={"displayName": "Ada"})
        assert response.status_code == 201
        body = response.json()
        assert body["displayName"] == "Ada"
        assert body["id"] > 0
        assert "createdAt" in body

    async def test_rejects_an_empty_name(self, client):
        response = await client.post("/users", json={"displayName": ""})
        assert response.status_code == 422

    async def test_rejects_a_name_over_the_column_limit(self, client):
        response = await client.post("/users", json={"displayName": "x" * 51})
        assert response.status_code == 422


class TestListTopics:
    """GET /topics."""

    async def test_lists_every_seeded_topic(self, client):
        response = await client.get("/topics")
        assert response.status_code == 200
        body = response.json()
        assert {t["slug"] for t in body} == {
            "derivatives",
            "logarithms",
            "trigonometry",
        }

    async def test_reports_a_usable_topic_id(self, client, topic_id):
        """The id this returns must be the one /next-question accepts."""
        body = (await client.get("/topics")).json()
        logs = next(t for t in body if t["slug"] == "logarithms")
        assert logs["id"] == topic_id

    async def test_counts_active_questions(self, client):
        body = (await client.get("/topics")).json()
        assert all(t["questionCount"] == 18 for t in body)

    async def test_excludes_retired_questions_from_the_count(
        self, client, session, topic_id
    ):
        await session.execute(
            update(Question)
            .where(Question.topic_id == topic_id)
            .values(is_active=False)
        )
        await session.flush()

        body = (await client.get("/topics")).json()
        logs = next(t for t in body if t["slug"] == "logarithms")
        assert logs["questionCount"] == 0


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
        """A new student sits at theta 0, so the nearest items are served.

        Difficulties drift as real answers land in the development
        database, so this checks the rule rather than a seeded value: the
        first question is one of the closest few to zero.
        """
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        nearest = list(
            await session.scalars(
                select(Question.id)
                .where(
                    Question.topic_id == topic_id,
                    Question.is_active.is_(True),
                )
                .order_by(func.abs(Question.difficulty_b))
                .limit(selection.CANDIDATE_POOL_SIZE)
            )
        )
        assert body["question"]["id"] in nearest

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

        feedback = (await _answer(client, user_id, served["id"], option))[
            "feedback"
        ]

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
        question = await session.get(Question, served["id"])
        # Relative to the row as found: other students' answers already
        # sit on it in a development database.
        answered_before = question.times_answered
        correct_before = question.times_correct

        option = await _correct_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        await session.refresh(question)
        assert question.times_answered == answered_before + 1
        assert question.times_correct == correct_before + 1

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

    async def test_rejects_a_non_positive_id(self, client, user_id):
        """The same rule as the query params, so a client sees one answer."""
        response = await client.post(
            "/submit-answer",
            json={"userId": user_id, "questionId": 0, "selectedOptionId": 1},
        )
        assert response.status_code == 422


class TestTopicCompletion:
    """Working a topic to completion through the API."""

    async def test_answering_everything_correctly_completes_the_topic(
        self, client, user_id, topic_id, session
    ):
        """The full loop: 18 questions, then a completion signal."""
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()

        answered = 0
        while served["question"] is not None:
            qid = served["question"]["id"]
            option = await _correct_option_id(session, qid)
            served = (await _answer(client, user_id, qid, option))["next"]
            answered += 1
            assert answered <= 18, "served more questions than exist"

        assert answered == 18
        assert served["complete"] is True
        assert served["question"] is None

    async def test_a_wrong_answer_keeps_the_topic_incomplete(
        self, client, user_id, topic_id, session
    ):
        """One wrong answer must be revisited before the topic closes."""
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()

        first = True
        seen = 0
        while served["question"] is not None and seen < 18:
            qid = served["question"]["id"]
            option = (
                await _wrong_option_id(session, qid)
                if first
                else await _correct_option_id(session, qid)
            )
            first = False
            served = (await _answer(client, user_id, qid, option))["next"]
            seen += 1

        assert served["complete"] is False
        assert served["question"] is not None

        progress = (await client.get(f"/progress/{user_id}")).json()
        logs = next(t for t in progress["topics"] if t["slug"] == "logarithms")
        assert logs["summary"]["mastered"] == 17
        assert logs["summary"]["total"] == 18


class TestHealth:
    """GET /health."""

    async def test_reports_ok(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCors:
    """Cross-origin access from the frontend's dev server."""

    async def test_answers_a_preflight_from_the_frontend(self, client):
        response = await client.options(
            "/submit-answer",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        allowed = response.headers["access-control-allow-origin"]
        assert allowed == "http://localhost:3000"
        assert "POST" in response.headers["access-control-allow-methods"]

    async def test_refuses_an_unlisted_origin(self, client):
        """The allow-origin header is the grant; withholding it refuses."""
        response = await client.options(
            "/submit-answer",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in response.headers

    async def test_does_not_grant_credentials(self, client):
        """Identity is a userId in the payload, never a cookie."""
        response = await client.get(
            "/health", headers={"Origin": "http://localhost:3000"}
        )
        assert "access-control-allow-credentials" not in response.headers


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
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
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
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
        assert logs["summary"]["answered"] == 1
        assert logs["summary"]["correct"] == 0
        assert logs["summary"]["mastered"] == 0

    async def test_rejects_a_non_positive_id(self, client):
        response = await client.get("/progress/0")
        assert response.status_code == 422

    async def test_unknown_user_is_not_found(self, client):
        response = await client.get("/progress/99999999")
        assert response.status_code == 404


class TestWeakSpots:
    """What /progress reports about a student's weaknesses."""

    async def test_a_new_student_has_none(self, client, user_id):
        body = (await client.get(f"/progress/{user_id}")).json()
        assert all(t["weakSpots"] == [] for t in body["topics"])

    async def test_a_wrong_answer_names_the_concepts_behind_it(
        self, client, user_id, topic_id, session
    ):
        served = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        option = await _wrong_option_id(session, served["id"])
        await _answer(client, user_id, served["id"], option)

        expected = set(
            await session.scalars(
                select(Tag.slug)
                .join(QuestionTag, QuestionTag.tag_id == Tag.id)
                .where(QuestionTag.question_id == served["id"])
            )
        )

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")

        assert logs["weakSpots"]
        assert {w["slug"] for w in logs["weakSpots"]} <= expected
        assert all(w["name"] for w in logs["weakSpots"])
        for spot in logs["weakSpots"]:
            assert spot["wrong"] == 1
            assert spot["correct"] == 0
            assert spot["total"] >= 1

    async def test_a_spot_counts_where_its_questions_stand(
        self, client, user_id, topic_id, session
    ):
        """One wrong, one right on the same concept: the ring must agree."""
        first = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()["question"]
        await _answer(
            client,
            user_id,
            first["id"],
            await _wrong_option_id(session, first["id"]),
        )
        concept = first["tags"][-1]["slug"]

        second = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
                f"&tag={concept}&exclude={first['id']}"
            )
        ).json()["question"]
        await _answer(
            client,
            user_id,
            second["id"],
            await _correct_option_id(session, second["id"]),
        )

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
        spot = next(w for w in logs["weakSpots"] if w["slug"] == concept)
        assert spot["wrong"] == 1
        assert spot["correct"] == 1
        assert spot["total"] == len(
            await _tagged_ids(session, topic_id, concept)
        )
        assert logs["summary"]["mastered"] == 1
        assert logs["summary"]["wrong"] == 1

    async def test_a_correct_answer_creates_no_weak_spot(
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
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
        assert logs["weakSpots"] == []

    async def test_it_reports_at_most_three(
        self, client, user_id, topic_id, session
    ):
        """A dashboard card has room for three, not for everything."""
        for _ in range(5):
            served = (
                await client.get(
                    f"/next-question?userId={user_id}&topicId={topic_id}"
                )
            ).json()["question"]
            option = await _wrong_option_id(session, served["id"])
            await _answer(client, user_id, served["id"], option)

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
        assert 0 < len(logs["weakSpots"]) <= 3

    async def test_misses_on_two_questions_of_one_concept_both_count(
        self, client, user_id, topic_id, session
    ):
        """Steering makes three wrong answers share a concept; both count."""
        for _ in range(3):
            served = (
                await client.get(
                    f"/next-question?userId={user_id}&topicId={topic_id}"
                )
            ).json()["question"]
            option = await _wrong_option_id(session, served["id"])
            await _answer(client, user_id, served["id"], option)

        body = (await client.get(f"/progress/{user_id}")).json()
        logs = next(t for t in body["topics"] if t["slug"] == "logarithms")
        assert max(w["wrong"] for w in logs["weakSpots"]) > 1
        assert logs["summary"]["wrong"] == 3


class TestQuestionTags:
    """Tags on a served question, which make the steering visible."""

    async def test_a_served_question_names_its_concepts(
        self, client, user_id, topic_id
    ):
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        tags = body["question"]["tags"]
        assert len(tags) >= 2
        assert all(t["slug"] and t["name"] for t in tags)

    async def test_tags_are_ordered_most_specific_first(
        self, client, user_id, topic_id, session
    ):
        """A client showing one tag should show the rarest."""
        body = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).json()
        slugs = [t["slug"] for t in body["question"]["tags"]]

        counts = {}
        for slug in slugs:
            counts[slug] = await session.scalar(
                select(func.count())
                .select_from(QuestionTag)
                .join(Tag, Tag.id == QuestionTag.tag_id)
                .join(Question, Question.id == QuestionTag.question_id)
                .where(Tag.slug == slug, Question.topic_id == topic_id)
            )
        ordered = [counts[s] for s in slugs]
        assert ordered == sorted(ordered)

    async def test_tags_do_not_reveal_the_answer(
        self, client, user_id, topic_id
    ):
        """Tags name a method, never an outcome."""
        raw = (
            await client.get(
                f"/next-question?userId={user_id}&topicId={topic_id}"
            )
        ).text.lower()
        for forbidden in ("iscorrect", "misconception", "solution"):
            assert forbidden not in raw


class TestPractisingOneTag:
    """GET /next-question?tag= — drilling a single concept."""

    async def _slug_of_served(self, client, user_id, topic_id, tag=None):
        query = f"/next-question?userId={user_id}&topicId={topic_id}"
        if tag:
            query += f"&tag={tag}"
        return (await client.get(query)).json()

    async def test_every_served_question_carries_the_tag(
        self, client, user_id, topic_id, session
    ):
        for _ in range(12):
            body = await self._slug_of_served(
                client, user_id, topic_id, "log-definition"
            )
            if body["question"] is None:
                break
            slugs = {t["slug"] for t in body["question"]["tags"]}
            assert "log-definition" in slugs

            option = await _correct_option_id(session, body["question"]["id"])
            await _answer(client, user_id, body["question"]["id"], option)

    async def test_it_completes_when_that_concept_runs_out(
        self, client, user_id, topic_id, session
    ):
        """Finishing one tag must not claim the whole topic is done."""
        for _ in range(20):
            body = await self._slug_of_served(
                client, user_id, topic_id, "change-of-base"
            )
            if body["question"] is None:
                break
            option = await _correct_option_id(session, body["question"]["id"])
            await _answer(client, user_id, body["question"]["id"], option)

        assert body["complete"] is True

        unfiltered = await self._slug_of_served(client, user_id, topic_id)
        assert unfiltered["complete"] is False
        assert unfiltered["question"] is not None

    async def test_an_unknown_tag_serves_nothing(
        self, client, user_id, topic_id
    ):
        body = await self._slug_of_served(
            client, user_id, topic_id, "not-a-real-tag"
        )
        assert body["complete"] is True
        assert body["question"] is None

    async def test_omitting_the_tag_still_serves_the_whole_topic(
        self, client, user_id, topic_id
    ):
        body = await self._slug_of_served(client, user_id, topic_id)
        assert body["question"] is not None


async def _tagged_ids(session, topic_id, *slugs):
    rows = await session.scalars(
        select(QuestionTag.question_id)
        .join(Tag, Tag.id == QuestionTag.tag_id)
        .join(Question, Question.id == QuestionTag.question_id)
        .where(Tag.slug.in_(slugs), Question.topic_id == topic_id)
    )
    return set(rows)


class TestSessions:
    """GET /next-question?exclude=&tag=&tag= — one sitting, no repeats."""

    @staticmethod
    def _url(user_id, topic_id, exclude=(), tags=()):
        query = f"/next-question?userId={user_id}&topicId={topic_id}"
        query += "".join(f"&exclude={q}" for q in exclude)
        query += "".join(f"&tag={t}" for t in tags)
        return query

    async def test_excluded_questions_are_never_served(
        self, client, user_id, topic_id
    ):
        """Passing back everything served so far walks the whole topic once."""
        served = []
        for _ in range(30):
            body = (
                await client.get(self._url(user_id, topic_id, served))
            ).json()
            if body["complete"]:
                break
            assert body["question"]["id"] not in served
            served.append(body["question"]["id"])
        assert len(served) == 18

    async def test_exclusion_holds_in_the_answered_wrong_tier(
        self, client, user_id, topic_id, session
    ):
        """A question just got wrong must not come straight back."""
        body = (
            await client.get(
                self._url(user_id, topic_id, tags=["change-of-base"])
            )
        ).json()
        first = body["question"]["id"]
        served = [first]
        option = await _wrong_option_id(session, first)
        await _answer(client, user_id, first, option)

        for _ in range(20):
            body = (
                await client.get(
                    self._url(user_id, topic_id, served, ["change-of-base"])
                )
            ).json()
            if body["complete"]:
                break
            qid = body["question"]["id"]
            assert qid != first
            served.append(qid)
            await _answer(
                client, user_id, qid, await _correct_option_id(session, qid)
            )
        assert body["complete"] is True

        # With the rest mastered and the exclusion lifted, the wrong one is
        # offered again: the session, not the concept, is what ran out.
        again = (
            await client.get(
                self._url(user_id, topic_id, tags=["change-of-base"])
            )
        ).json()
        assert again["question"]["id"] == first

    async def test_reports_how_many_remain_in_the_pool(
        self, client, user_id, topic_id, session
    ):
        """A session sizes its bar from this, so it must count exactly."""
        fresh = (await client.get(self._url(user_id, topic_id))).json()
        assert fresh["remaining"] == 18

        served = [fresh["question"]["id"]]
        after_one = (
            await client.get(self._url(user_id, topic_id, served))
        ).json()
        assert after_one["remaining"] == 17

        concept = (
            await client.get(
                self._url(user_id, topic_id, tags=["change-of-base"])
            )
        ).json()
        assert concept["remaining"] == len(
            await _tagged_ids(session, topic_id, "change-of-base")
        )

    async def test_several_tags_pool_the_union(
        self, client, user_id, topic_id, session
    ):
        expected = await _tagged_ids(
            session, topic_id, "change-of-base", "log-definition"
        )
        served = []
        for _ in range(30):
            body = (
                await client.get(
                    self._url(
                        user_id,
                        topic_id,
                        served,
                        ["change-of-base", "log-definition"],
                    )
                )
            ).json()
            if body["complete"]:
                break
            served.append(body["question"]["id"])
        assert set(served) == expected
        assert len(expected) > len(
            await _tagged_ids(session, topic_id, "change-of-base")
        )
