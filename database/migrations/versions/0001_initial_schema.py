"""initial schema: incidents, investigations, evidence, reports

Revision ID: 0001
Revises:
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.id"),
            nullable=True,
        ),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("agent_status", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id"),
            nullable=False,
        ),
        sa.Column("agent", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence_signal", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("body", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("evidence")
    op.drop_table("investigations")
    op.drop_table("incidents")
