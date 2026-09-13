"""SQLAlchemy models for the adaptive quiz schema.

`docs/data-model.md` is the annotated reference for these tables and
explains why the non-obvious constraints exist.
"""

import datetime
import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Double,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TIMESTAMP, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_UINT = INTEGER(unsigned=True)
_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


class Base(DeclarativeBase):
    """Declarative base for every model in the project."""


class DifficultyLabel(enum.StrEnum):
    """Authored difficulty band, frozen after authoring."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


#: Starting `difficulty_b` for each authored label, on the logit scale.
LABEL_TO_INITIAL_B: dict[DifficultyLabel, float] = {
    DifficultyLabel.EASY: -1.0,
    DifficultyLabel.MEDIUM: 0.0,
    DifficultyLabel.HARD: 1.0,
}


class Topic(Base):
    """A subject area that ability is tracked against."""

    __tablename__ = "topics"
    __table_args__ = _TABLE_ARGS

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Question(Base):
    """A multiple-choice question and its live difficulty estimate."""

    __tablename__ = "questions"
    __table_args__ = (
        Index("idx_topic_b", "topic_id", "is_active", "difficulty_b"),
        CheckConstraint(
            "times_correct <= times_answered",
            name="ck_correct_lte_answered",
        ),
        _TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    topic_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("topics.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stem: Mapped[str] = mapped_column(String(1000), nullable=False)
    difficulty_label: Mapped[DifficultyLabel] = mapped_column(
        Enum(
            DifficultyLabel,
            values_callable=lambda e: [m.value for m in e],
            name="difficulty_label",
        ),
        nullable=False,
    )
    difficulty_b: Mapped[float] = mapped_column(Double, nullable=False)
    # MySQL stores boolean defaults as '1'/'0'. Writing them that way here
    # keeps autogenerate from emitting a no-op alter on every revision.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )
    times_answered: Mapped[int] = mapped_column(
        _UINT,
        nullable=False,
        server_default=text("0"),
    )
    times_correct: Mapped[int] = mapped_column(
        _UINT,
        nullable=False,
        server_default=text("0"),
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )


class QuestionOption(Base):
    """One answer choice belonging to a question."""

    __tablename__ = "question_options"
    __table_args__ = (
        UniqueConstraint("question_id", "correct_flag", name="uq_one_correct"),
        UniqueConstraint("question_id", "position", name="uq_position"),
        # Redundant by itself, but gives attempts a composite foreign-key
        # target so an attempt cannot pair a question with another
        # question's option.
        UniqueConstraint("question_id", "id", name="uq_question_option"),
        CheckConstraint(
            "is_correct = FALSE OR misconception IS NULL",
            name="ck_no_misconception_on_correct",
        ),
        _TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
    )
    # MySQL unique indexes ignore NULLs, so uq_one_correct permits unlimited
    # incorrect options but only one correct option per question.
    correct_flag: Mapped[int | None] = mapped_column(
        TINYINT(unsigned=True),
        Computed("IF(is_correct, 1, NULL)", persisted=True),
    )
    position: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )
    # Student-facing note naming the specific error this choice encodes.
    # Null on the correct option, which the check constraint enforces.
    misconception: Mapped[str | None] = mapped_column(String(500))


class QuestionStep(Base):
    """One line of a question's worked solution.

    Shown only after an answer is submitted, since the steps give away
    the correct answer.
    """

    __tablename__ = "question_steps"
    __table_args__ = (
        UniqueConstraint("question_id", "step_number", name="uq_step_number"),
        _TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(String(500), nullable=False)


class Tag(Base):
    """A concept a question exercises, such as the product rule.

    Questions carry several, and two questions are alike to the extent
    their tags overlap. That is what makes "practise something similar"
    possible without a hand-built map of which question follows which.
    """

    __tablename__ = "tags"
    __table_args__ = _TABLE_ARGS

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class QuestionTag(Base):
    """Joins a question to one of its tags."""

    __tablename__ = "question_tags"
    __table_args__ = (
        Index("idx_tag", "tag_id"),
        _TABLE_ARGS,
    )

    question_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # RESTRICT, not CASCADE: deleting a tag that questions still carry
    # would silently make them less similar to everything, which is the
    # kind of change that should be deliberate.
    tag_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("tags.id", ondelete="RESTRICT"),
        primary_key=True,
    )


class User(Base):
    """A student. No authentication exists in this project by design."""

    __tablename__ = "users"
    __table_args__ = _TABLE_ARGS

    id: Mapped[int] = mapped_column(_UINT, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


class UserTopicAbility(Base):
    """A student's current ability estimate within one topic."""

    __tablename__ = "user_topic_ability"
    __table_args__ = (
        Index("idx_topic", "topic_id"),
        _TABLE_ARGS,
    )

    user_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theta: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text("0"),
    )
    attempts_count: Mapped[int] = mapped_column(
        _UINT,
        nullable=False,
        server_default=text("0"),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )


class Attempt(Base):
    """An immutable record of one answer and the update it produced."""

    __tablename__ = "attempts"
    __table_args__ = (
        # Pairs the option to its question in one constraint, which also
        # supplies the index for the standalone question_id foreign key.
        ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["question_options.question_id", "question_options.id"],
            name="fk_attempt_option_matches_question",
            ondelete="RESTRICT",
        ),
        Index("idx_user_topic_time", "user_id", "topic_id", "answered_at"),
        _TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    topic_id: Mapped[int] = mapped_column(
        _UINT,
        ForeignKey("topics.id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_option_id: Mapped[int] = mapped_column(_UINT, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    theta_before: Mapped[float] = mapped_column(Double, nullable=False)
    theta_after: Mapped[float] = mapped_column(Double, nullable=False)
    b_before: Mapped[float] = mapped_column(Double, nullable=False)
    b_after: Mapped[float] = mapped_column(Double, nullable=False)
    k_theta: Mapped[float] = mapped_column(Double, nullable=False)
    k_b: Mapped[float] = mapped_column(Double, nullable=False)
    answered_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(fsp=3),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(3)"),
    )
