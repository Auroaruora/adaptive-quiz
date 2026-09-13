"""Add question tags, so "something similar" has a meaning.

Two questions are alike to the extent their tags overlap, which is what
lets the app answer a repeated mistake with related practice rather than
whatever happens to sit nearby on the difficulty scale.

question_tags cascades from its question but RESTRICTs on its tag:
deleting a question should take its tags with it, while deleting a tag
that questions still carry would quietly make them less similar to
everything, and that should be a deliberate act.


Revision ID: 713bf0335de6
Revises: 70818f857b05
Create Date: 2026-09-13 18:56:44.392384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '713bf0335de6'
down_revision: Union[str, Sequence[str], None] = '70818f857b05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the tag vocabulary and the question-to-tag join."""
    op.create_table('tags',
    sa.Column('id', mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_engine='InnoDB'
    )
    op.create_table('question_tags',
    sa.Column('question_id', mysql.INTEGER(unsigned=True), nullable=False),
    sa.Column('tag_id', mysql.INTEGER(unsigned=True), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('question_id', 'tag_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_engine='InnoDB'
    )
    op.create_index('idx_tag', 'question_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    """Drops the join first, since it references both tables."""
    op.drop_index('idx_tag', table_name='question_tags')
    op.drop_table('question_tags')
    op.drop_table('tags')
