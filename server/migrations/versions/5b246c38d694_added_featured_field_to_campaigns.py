"""added featured field to campaigns

Revision ID: 5b246c38d694
Revises: 86e046f57ae5
Create Date: 2024-04-12 12:05:43.869195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b246c38d694'
down_revision = '86e046f57ae5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('campaigns', sa.Column('featured', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('campaigns', 'featured')
    # ### end Alembic commands ###
