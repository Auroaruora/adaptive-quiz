"""Serving questions and grading answers."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import irt, schemas, services
from app.db.models import (
    Attempt,
    Question,
    QuestionOption,
    Topic,
    User,
)
from app.db.session import get_session

router = APIRouter(tags=["quiz"])


async def _require(session: AsyncSession, model, key, what: str):
    """Loads a row by primary key or raises 404.

    Args:
        session: Open async session.
        model: Mapped class to load.
        key: Primary key value.
        what: Noun used in the error message.

    Returns:
        The loaded row.

    Raises:
        HTTPException: 404 when no such row exists.
    """
    row = await session.get(model, key)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{what} {key} does not exist",
        )
    return row


@router.get("/next-question", response_model=schemas.NextQuestionOut)
async def next_question(
    user_id: int = Query(alias="userId", gt=0),
    topic_id: int = Query(alias="topicId", gt=0),
    tag: list[str] = Query(default=[]),
    exclude: list[int] = Query(default=[]),
    session: AsyncSession = Depends(get_session),
) -> schemas.NextQuestionOut:
    """Serves the next question, optionally narrowed.

    Args:
        user_id: Student to serve.
        topic_id: Topic to serve from.
        tag: Repeatable. Restricts the pool to questions carrying any of
            these concepts, for practising weak spots. Omit to serve the
            whole topic.
        exclude: Repeatable. Question ids already asked this session,
            which are never served again however the tiers fall.
        session: Injected database session.

    Returns:
        The next question, or a completion signal meaning nothing is left
        after the narrowing: the whole topic, those concepts, or this
        session's pool.
    """
    await _require(session, User, user_id, "user")
    await _require(session, Topic, topic_id, "topic")

    ability = await services.get_or_create_ability(
        session, user_id=user_id, topic_id=topic_id
    )
    await session.commit()

    return await services.next_question_payload(
        session,
        user_id=user_id,
        topic_id=topic_id,
        theta=ability.theta,
        tag_slugs=tag,
        exclude=exclude,
    )


@router.post("/submit-answer", response_model=schemas.SubmitAnswerOut)
async def submit_answer(
    body: schemas.AnswerCreate,
    session: AsyncSession = Depends(get_session),
) -> schemas.SubmitAnswerOut:
    """Grades an answer, updates both parameters, and serves the next one.

    Everything the answer touches moves together in one transaction: the
    student's ability, the question's difficulty and answer counters, and
    the attempt row that makes the update replayable.

    Args:
        body: The student's answer.
        session: Injected database session.

    Returns:
        Feedback on this answer, followed by the next question.

    Raises:
        HTTPException: 404 if the user, question or option is unknown;
            400 if the option belongs to a different question.
    """
    user = await _require(session, User, body.user_id, "user")
    question = await _require(session, Question, body.question_id, "question")
    chosen = await _require(
        session, QuestionOption, body.selected_option_id, "option"
    )

    if chosen.question_id != question.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"option {chosen.id} belongs to question "
                f"{chosen.question_id}, not {question.id}"
            ),
        )

    ability = await services.get_or_create_ability(
        session, user_id=user.id, topic_id=question.topic_id
    )

    update = irt.apply_answer(
        theta=ability.theta,
        difficulty=question.difficulty_b,
        times_answered=question.times_answered,
        is_correct=chosen.is_correct,
    )

    ability.theta = update.theta_after
    ability.attempts_count += 1
    question.difficulty_b = update.b_after
    question.times_answered += 1
    question.times_correct += int(chosen.is_correct)

    session.add(
        Attempt(
            user_id=user.id,
            question_id=question.id,
            topic_id=question.topic_id,
            selected_option_id=chosen.id,
            is_correct=chosen.is_correct,
            theta_before=update.theta_before,
            theta_after=update.theta_after,
            b_before=update.b_before,
            b_after=update.b_after,
            k_theta=update.k_theta,
            k_b=update.k_b,
        )
    )
    await session.commit()

    correct_option_id = await session.scalar(
        QuestionOption.__table__.select()
        .with_only_columns(QuestionOption.id)
        .where(
            QuestionOption.question_id == question.id,
            QuestionOption.is_correct.is_(True),
        )
    )

    feedback = schemas.FeedbackOut(
        is_correct=chosen.is_correct,
        correct_option_id=correct_option_id,
        misconception=None if chosen.is_correct else chosen.misconception,
        solution=await services.solution_steps(session, question.id),
        theta_before=update.theta_before,
        theta_after=update.theta_after,
    )

    return schemas.SubmitAnswerOut(
        feedback=feedback,
        next=await services.next_question_payload(
            session,
            user_id=user.id,
            topic_id=question.topic_id,
            theta=update.theta_after,
        ),
    )
