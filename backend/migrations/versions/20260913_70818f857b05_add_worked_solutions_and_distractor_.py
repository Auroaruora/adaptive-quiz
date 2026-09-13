"""Add worked solutions and per-distractor feedback.

Gives a wrong answer something to teach with, rather than just marking it
wrong:

- `question_steps` holds the worked solution, one row per step, ordered by
  `step_number`. A table rather than a JSON column because the steps are
  real content that benefits from being queryable and individually
  editable, and `uq_step_number` guarantees the ordering has no gaps or
  duplicates at the database level.
- `question_options.misconception` names the specific error a wrong choice
  encodes, so the student is told what they did rather than being left to
  diff their work against a model solution. It is null on the correct
  option, which `ck_no_misconception_on_correct` enforces.

Both are answer-revealing and must never be sent to the frontend before an
answer is submitted.

The check constraint is written by hand: Alembic's autogenerate does not
detect CHECK constraints, so it would be silently dropped from any future
revision that regenerates this table.

Revision ID: 70818f857b05
Revises: 9fb0defd7b0c
Create Date: 2026-09-13 15:17:00.740682

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "70818f857b05"
down_revision: Union[str, Sequence[str], None] = "9fb0defd7b0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adds the worked-solution table and the distractor feedback column."""
    op.create_table(
        "question_steps",
        sa.Column("id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("question_id", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("step_number", mysql.TINYINT(unsigned=True), nullable=False),
        sa.Column("body", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "question_id", "step_number", name="uq_step_number"
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        mysql_engine="InnoDB",
    )
    op.add_column(
        "question_options",
        sa.Column("misconception", sa.String(length=500), nullable=True),
    )
    op.create_check_constraint(
        "ck_no_misconception_on_correct",
        "question_options",
        "is_correct = FALSE OR misconception IS NULL",
    )


def downgrade() -> None:
    """Drops both, constraint first so the column is free to go."""
    op.drop_constraint(
        "ck_no_misconception_on_correct",
        "question_options",
        type_="check",
    )
    op.drop_column("question_options", "misconception")
    op.drop_table("question_steps")
