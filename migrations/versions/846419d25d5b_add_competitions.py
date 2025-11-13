"""add competitions

Revision ID: 846419d25d5b
Revises: fe66660cb2cd
Create Date: 2025-11-13 10:31:29.026547

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '846419d25d5b'
down_revision = 'fe66660cb2cd'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'competition' not in inspector.get_table_names():
        op.create_table('competition',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('category', sa.Enum('internal', 'external'), nullable=False),
    sa.Column('level', sa.Enum('国际级', '国家级', '区域级', '省级', '市级', '校级', '联合赛', '企业赛', '邀请赛'), nullable=False),
    sa.Column('department_id', sa.BigInteger(), nullable=True),
    sa.Column('event_date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['department_id'], ['department.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    if 'competition_result' not in inspector.get_table_names():
        op.create_table('competition_result',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('competition_id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('score', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('award', sa.String(length=64), nullable=True),
    sa.Column('remark', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['competition_id'], ['competition.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('competition_id', 'user_id', name='uniq_competition_user')
    )
    


def downgrade():
    op.drop_table('competition_result')
    op.drop_table('competition')
