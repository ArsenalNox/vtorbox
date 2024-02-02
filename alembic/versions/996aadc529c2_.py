"""empty message

Revision ID: 996aadc529c2
Revises: 8dbded9fc6e5
Create Date: 2023-12-28 08:22:14.819603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '996aadc529c2'
down_revision: Union[str, None] = '8dbded9fc6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('on_interval', sa.Boolean(), nullable=True))
    op.add_column('orders', sa.Column('interval_type', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('intreval', sa.String(), nullable=True))
    op.drop_column('orders', 'interval')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('interval', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('orders', 'intreval')
    op.drop_column('orders', 'interval_type')
    op.drop_column('orders', 'on_interval')
    # ### end Alembic commands ###
