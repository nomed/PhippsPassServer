"""empty message

Revision ID: cddac56a1454
Revises: 264d14556923
Create Date: 2019-02-24 03:29:30.727573

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cddac56a1454'
down_revision = '264d14556923'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pass_device_association',
    sa.Column('pass_id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['device.id'], ),
    sa.ForeignKeyConstraint(['pass_id'], ['pass.id'], ),
    sa.PrimaryKeyConstraint('pass_id', 'device_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pass_device_association')
    # ### end Alembic commands ###