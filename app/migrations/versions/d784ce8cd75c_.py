"""empty message

Revision ID: d784ce8cd75c
Revises: 87ad9f142151
Create Date: 2019-02-24 02:24:30.183921

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd784ce8cd75c'
down_revision = '87ad9f142151'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('member_pass_association',
    sa.Column('member_id', sa.String(length=100), nullable=True),
    sa.Column('pass_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], ),
    sa.ForeignKeyConstraint(['pass_id'], ['pass.id'], )
    )
    op.drop_table('member_pass')
    op.add_column('device', sa.Column('id', sa.Integer(), nullable=False))
    op.drop_column('device', 'device_lib_id')
    op.drop_column('device', 'push_token')
    op.add_column('member', sa.Column('expiration_date', sa.DateTime(), nullable=True))
    op.alter_column('member', 'address_line_1',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('member', 'city',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('member', 'state',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.alter_column('member', 'status',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('member', 'zip',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)
    op.drop_constraint('pass_member_id_fkey', 'pass', type_='foreignkey')
    op.drop_column('pass', 'active')
    op.drop_column('pass', 'membership_level')
    op.drop_column('pass', 'member_id')
    op.drop_column('pass', 'expiration_date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pass', sa.Column('expiration_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('pass', sa.Column('member_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.add_column('pass', sa.Column('membership_level', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('pass', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.create_foreign_key('pass_member_id_fkey', 'pass', 'member', ['member_id'], ['id'])
    op.alter_column('member', 'zip',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('member', 'status',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('member', 'state',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('member', 'city',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.alter_column('member', 'address_line_1',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
    op.drop_column('member', 'expiration_date')
    op.add_column('device', sa.Column('push_token', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('device', sa.Column('device_lib_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
    op.drop_column('device', 'id')
    op.create_table('member_pass',
    sa.Column('member_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('pass_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['member_id'], ['member.id'], name='member_pass_member_id_fkey'),
    sa.ForeignKeyConstraint(['pass_id'], ['pass.id'], name='member_pass_pass_id_fkey'),
    sa.PrimaryKeyConstraint('member_id', 'pass_id', name='member_pass_pkey')
    )
    op.drop_table('member_pass_association')
    # ### end Alembic commands ###