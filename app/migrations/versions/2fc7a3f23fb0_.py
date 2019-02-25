"""empty message

Revision ID: 2fc7a3f23fb0
Revises: 9f3b8633dfda
Create Date: 2019-02-24 03:11:17.289066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fc7a3f23fb0'
down_revision = '9f3b8633dfda'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pass_device_association',
    sa.Column('pass_id', sa.Integer(), nullable=True),
    sa.Column('device_device_lib_id', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['device_device_lib_id'], ['device.device_lib_id'], ),
    sa.ForeignKeyConstraint(['pass_id'], ['pass.id'], )
    )
    op.create_unique_constraint(None, 'device', ['device_lib_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'device', type_='unique')
    op.drop_table('pass_device_association')
    # ### end Alembic commands ###