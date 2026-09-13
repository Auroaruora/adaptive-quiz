"""Initial schema for the adaptive quiz.

Creates all six v1 tables. Three choices here are not obvious from the
DDL alone, and are explained at length in docs/data-model.md:

- `question_options.correct_flag` is generated as 1-or-NULL rather than
  indexing `is_correct` directly, because MySQL unique indexes ignore
  NULLs. That is what lets `uq_one_correct` permit many incorrect options
  but only one correct one, without a circular foreign key back to
  `questions`.
- `uq_question_option` is redundant on its own. It exists solely to give
  `attempts` a composite foreign-key target, so an attempt cannot pair a
  question with an option belonging to a different question.
- `attempts` stores both parameters either side of the update plus the
  step sizes used, so any historical update can be replayed and verified
  even after the learning rates are retuned.

Revision ID: 9fb0defd7b0c
Revises:
Create Date: 2026-09-13 14:49:55.015880

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "9fb0defd7b0c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "topics",
        sa.Column("id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            mysql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_table(
        "users",
        sa.Column("id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("display_name", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            mysql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_table(
        "questions",
        sa.Column("id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("topic_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("stem", sa.String(length=1000), nullable=False),
        sa.Column(
            "difficulty_label",
            sa.Enum("easy", "medium", "hard", name="difficulty_label"),
            nullable=False,
        ),
        sa.Column("difficulty_b", sa.Double(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("TRUE"),
            nullable=False,
        ),
        sa.Column(
            "times_answered",
            mysql.INTEGER(unsigned=True),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "times_correct",
            mysql.INTEGER(unsigned=True),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            mysql.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.TIMESTAMP(),
            server_default=sa.text(
                "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "times_correct <= times_answered", name="ck_correct_lte_answered"
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "idx_topic_b",
        "questions",
        ["topic_id", "is_active", "difficulty_b"],
        unique=False,
    )
    op.create_table(
        "user_topic_ability",
        sa.Column("user_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("topic_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column(
            "theta", sa.Double(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "attempts_count",
            mysql.INTEGER(unsigned=True),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            mysql.TIMESTAMP(),
            server_default=sa.text(
                "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "idx_topic", "user_topic_ability", ["topic_id"], unique=False
    )
    op.create_table(
        "question_options",
        sa.Column("id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("question_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("option_text", sa.String(length=500), nullable=False),
        sa.Column(
            "is_correct",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "correct_flag",
            mysql.TINYINT(unsigned=True),
            sa.Computed("IF(is_correct, 1, NULL)", persisted=True),
            nullable=True,
        ),
        sa.Column("position", mysql.TINYINT(unsigned=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id", "correct_flag", name="uq_one_correct"
        ),
        sa.UniqueConstraint("question_id", "id", name="uq_question_option"),
        sa.UniqueConstraint("question_id", "position", name="uq_position"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_table(
        "attempts",
        sa.Column("id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("question_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("topic_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column(
            "selected_option_id", mysql.INTEGER(unsigned=True), nullable=False
        ),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("theta_before", sa.Double(), nullable=False),
        sa.Column("theta_after", sa.Double(), nullable=False),
        sa.Column("b_before", sa.Double(), nullable=False),
        sa.Column("b_after", sa.Double(), nullable=False),
        sa.Column("k_theta", sa.Double(), nullable=False),
        sa.Column("k_b", sa.Double(), nullable=False),
        sa.Column(
            "answered_at",
            mysql.TIMESTAMP(fsp=3),
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["question_options.question_id", "question_options.id"],
            name="fk_attempt_option_matches_question",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "idx_user_topic_time",
        "attempts",
        ["user_id", "topic_id", "answered_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drops every table, children first.

    Alembic's generated version dropped each index before its table. That
    fails with error 1553: every one of these indexes leads with a
    foreign-key column, so MySQL adopted it as the index backing that
    constraint rather than building a duplicate, and it cannot be dropped
    while the constraint exists. DROP TABLE removes a table's indexes
    anyway, so the explicit drops were never needed.
    """
    op.drop_table("attempts")
    op.drop_table("question_options")
    op.drop_table("user_topic_ability")
    op.drop_table("questions")
    op.drop_table("users")
    op.drop_table("topics")
