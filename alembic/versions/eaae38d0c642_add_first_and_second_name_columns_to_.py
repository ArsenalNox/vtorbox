"""add first and second name columns to user model

Revision ID: eaae38d0c642
Revises: 
Create Date: 2023-12-25 13:08:14.097658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaae38d0c642'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # op.drop_column('users', 'full_name')

    # op.add_column('users', 'user_firstname', sa.Column(sa.String(), nullable=True))
    # op.add_column('users', 'user_secondname', sa.Column(sa.String(), nullable=True))
    pass

def downgrade() -> None:
    pass
