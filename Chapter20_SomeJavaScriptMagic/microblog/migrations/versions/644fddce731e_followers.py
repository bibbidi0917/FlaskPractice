"""followers

Revision ID: 644fddce731e
Revises: 17404d501f26
Create Date: 2021-12-07 16:14:09.920881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '644fddce731e'
down_revision = '17404d501f26'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
