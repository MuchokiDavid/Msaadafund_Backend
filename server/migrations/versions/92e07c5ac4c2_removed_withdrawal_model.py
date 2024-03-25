"""Removed withdrawal model

Revision ID: 92e07c5ac4c2
Revises: 6ccfca3d6811
Create Date: 2024-03-25 18:03:00.002326

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92e07c5ac4c2'
down_revision = '6ccfca3d6811'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('withdrawals')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('withdrawals',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('amount', sa.FLOAT(), nullable=False),
    sa.Column('status', sa.VARCHAR(), nullable=True),
    sa.Column('withdraw_method', sa.VARCHAR(), nullable=True),
    sa.Column('intasend_id', sa.VARCHAR(), nullable=True),
    sa.Column('transaction_date', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('campaign_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
