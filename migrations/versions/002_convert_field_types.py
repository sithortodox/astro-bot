"""convert field types

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

"""
from typing import Sequence, Union
from datetime import datetime, date

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def parse_birth_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%d.%m.%Y").date()
    except (ValueError, TypeError):
        return None


def parse_iso_datetime(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def parse_date_str(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def upgrade() -> None:
    conn = op.get_bind()

    users = sa.table('users',
        sa.column('id', sa.Integer),
        sa.column('birth_date', sa.String(10)),
        sa.column('premium_until', sa.String(30)),
        sa.column('last_request_date', sa.String(10)),
    )

    rows = conn.execute(sa.select(users.c.id, users.c.birth_date, users.c.premium_until, users.c.last_request_date)).fetchall()

    op.alter_column('users', 'birth_date', type_=sa.Date(), nullable=True)
    op.alter_column('users', 'premium_until', type_=sa.DateTime(timezone=True), nullable=True)
    op.alter_column('users', 'last_request_date', type_=sa.Date(), nullable=True)

    for row in rows:
        uid = row[0]
        bd = parse_birth_date(row[1])
        pu = parse_iso_datetime(row[2])
        lr = parse_date_str(row[3])

        updates = []
        if bd is not None:
            updates.append(('birth_date', bd))
        if pu is not None:
            updates.append(('premium_until', pu))
        if lr is not None:
            updates.append(('last_request_date', lr))

        if updates:
            from sqlalchemy import text
            set_parts = [f"{col} = :{col}" for col, _ in updates]
            params = {col: val for col, val in updates}
            params['uid'] = uid
            conn.execute(text(f"UPDATE users SET {', '.join(set_parts)} WHERE id = :uid"), params)


def downgrade() -> None:
    conn = op.get_bind()

    users = sa.table('users',
        sa.column('id', sa.Integer),
        sa.column('birth_date', sa.Date),
        sa.column('premium_until', sa.DateTime),
        sa.column('last_request_date', sa.Date),
    )

    rows = conn.execute(sa.select(users.c.id, users.c.birth_date, users.c.premium_until, users.c.last_request_date)).fetchall()

    op.alter_column('users', 'birth_date', type_=sa.String(10), nullable=True)
    op.alter_column('users', 'premium_until', type_=sa.String(30), nullable=True)
    op.alter_column('users', 'last_request_date', type_=sa.String(10), nullable=True)

    for row in rows:
        uid = row[0]
        bd = row[1].strftime("%d.%m.%Y") if row[1] else None
        pu = row[2].isoformat() if row[2] else None
        lr = row[3].strftime("%Y-%m-%d") if row[3] else None

        from sqlalchemy import text
        conn.execute(
            text("UPDATE users SET birth_date = :bd, premium_until = :pu, last_request_date = :lr WHERE id = :uid"),
            {"bd": bd, "pu": pu, "lr": lr, "uid": uid},
        )
