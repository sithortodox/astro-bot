"""convert field types

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # birth_date: "DD.MM.YYYY" → DATE via temp column
    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN birth_date_new DATE;
        UPDATE users SET birth_date_new = TO_DATE(birth_date, 'DD.MM.YYYY') WHERE birth_date ~ '^\\d{2}\\.\\d{2}\\.\\d{4}$';
        ALTER TABLE users DROP COLUMN birth_date;
        ALTER TABLE users RENAME COLUMN birth_date_new TO birth_date;
    """))

    # premium_until: ISO string → TIMESTAMP WITH TIME ZONE
    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN premium_until_new TIMESTAMP WITH TIME ZONE;
        UPDATE users SET premium_until_new = premium_until::timestamp with time zone WHERE premium_until IS NOT NULL AND premium_until != '';
        ALTER TABLE users DROP COLUMN premium_until;
        ALTER TABLE users RENAME COLUMN premium_until_new TO premium_until;
    """))

    # last_request_date: "YYYY-MM-DD" → DATE
    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN last_request_date_new DATE;
        UPDATE users SET last_request_date_new = last_request_date::date WHERE last_request_date IS NOT NULL AND last_request_date != '';
        ALTER TABLE users DROP COLUMN last_request_date;
        ALTER TABLE users RENAME COLUMN last_request_date_new TO last_request_date;
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN birth_date_old VARCHAR(10);
        UPDATE users SET birth_date_old = TO_CHAR(birth_date, 'DD.MM.YYYY') WHERE birth_date IS NOT NULL;
        ALTER TABLE users DROP COLUMN birth_date;
        ALTER TABLE users RENAME COLUMN birth_date_old TO birth_date;
    """))

    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN premium_until_old VARCHAR(30);
        UPDATE users SET premium_until_old = premium_until::text WHERE premium_until IS NOT NULL;
        ALTER TABLE users DROP COLUMN premium_until;
        ALTER TABLE users RENAME COLUMN premium_until_old TO premium_until;
    """))

    conn.execute(sa.text("""
        ALTER TABLE users ADD COLUMN last_request_date_old VARCHAR(10);
        UPDATE users SET last_request_date_old = TO_CHAR(last_request_date, 'YYYY-MM-DD') WHERE last_request_date IS NOT NULL;
        ALTER TABLE users DROP COLUMN last_request_date;
        ALTER TABLE users RENAME COLUMN last_request_date_old TO last_request_date;
    """))
