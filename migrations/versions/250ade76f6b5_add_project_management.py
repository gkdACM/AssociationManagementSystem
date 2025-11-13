"""add project management

Revision ID: 250ade76f6b5
Revises: 846419d25d5b
Create Date: 2025-11-13 10:57:17.761356

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '250ade76f6b5'
down_revision = '846419d25d5b'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'project' not in inspector.get_table_names():
        op.create_table('project',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('department_id', sa.BigInteger(), nullable=True),
    sa.Column('leader_user_id', sa.BigInteger(), nullable=False),
    sa.Column('github_url', sa.String(length=255), nullable=True),
    sa.Column('status', sa.Enum('draft', 'active', 'pending_acceptance', 'accepted', 'rejected'), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
    sa.ForeignKeyConstraint(['leader_user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    if 'project_participation' not in inspector.get_table_names():
        op.create_table('project_participation',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('project_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'approved', 'rejected'), nullable=False),
    sa.Column('remark', sa.String(length=255), nullable=True),
    sa.Column('applied_at', sa.DateTime(), nullable=False),
    sa.Column('decided_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'user_id', name='uniq_project_user')
    )
    # 保留原有考试表，避免外键冲突
    # ### end Alembic commands ###


def downgrade():
    op.drop_table('project_participation')
    op.drop_table('project')
    # ### end Alembic commands ###
