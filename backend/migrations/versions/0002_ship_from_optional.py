"""make ship-from optional on items

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-28 13:32:15.008397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('ship_from_country', existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column('ship_from_postcode', existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('ship_from_postcode', existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column('ship_from_country', existing_type=sa.VARCHAR(), nullable=False)
