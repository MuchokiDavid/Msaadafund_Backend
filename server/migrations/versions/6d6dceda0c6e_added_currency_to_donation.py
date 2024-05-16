"""Added currency to donation

Revision ID: 6d6dceda0c6e
Revises: cdbeb0047899
Create Date: 2024-05-16 21:55:32.030239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d6dceda0c6e'
down_revision = 'cdbeb0047899'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('donations', sa.Column('currency', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('donations', 'currency')
    # ### end Alembic commands ###
