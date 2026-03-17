"""init schema

Revision ID: 0001_init
Revises: 
Create Date: 2026-03-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE match_status AS ENUM ('scheduled', 'live', 'finished')")

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("balance", sa.Float(), nullable=False, server_default=sa.text("100.0")),
    )

    op.create_table(
        "matches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("team1", sa.String(), nullable=False),
        sa.Column("team2", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("scheduled", "live", "finished", name="match_status"),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("winner", sa.String(), nullable=True),
        sa.Column("coef_team1", sa.Float(), nullable=False, server_default=sa.text("2.0")),
        sa.Column("coef_team2", sa.Float(), nullable=False, server_default=sa.text("2.0")),
    )

    op.create_table(
        "bets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("match_id", sa.BigInteger(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("team", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("coef", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("ix_bets_user_id", "bets", ["user_id"])
    op.create_index("ix_bets_match_id", "bets", ["match_id"])


def downgrade() -> None:
    op.drop_index("ix_bets_match_id", table_name="bets")
    op.drop_index("ix_bets_user_id", table_name="bets")
    op.drop_table("bets")
    op.drop_table("matches")
    op.drop_table("users")
    op.execute("DROP TYPE match_status")

