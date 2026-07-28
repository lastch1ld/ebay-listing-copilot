"""add item defects

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-28 13:40:04.644952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'items', sa.Column('defects', sa.String(), nullable=False, server_default='')
    )


def downgrade() -> None:
    with op.batch_alter_table('items') as batch_op:
        batch_op.drop_column('defects')
