"""initial

Revision ID: 001
Revises: 
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('zodiac_sign', sa.String(50), nullable=True),
        sa.Column('birth_date', sa.String(10), nullable=True),
        sa.Column('birth_time', sa.String(5), nullable=True),
        sa.Column('birth_place', sa.String(255), nullable=True),
        sa.Column('is_premium', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('premium_until', sa.String(30), nullable=True),
        sa.Column('subscription_type', sa.String(20), nullable=True),
        sa.Column('daily_requests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_request_date', sa.String(10), nullable=True),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('total_requests', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

    op.create_table(
        'history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('command', sa.String(50), nullable=False),
        sa.Column('result', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_history_user_id', 'history', ['user_id'])
    op.create_index('ix_history_created_at', 'history', ['created_at'])

    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('generations_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), server_default='created', nullable=False),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id'),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_payment_id', 'payments', ['payment_id'])


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('history')
    op.drop_table('users')
