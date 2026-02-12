"""add trip messages table

Revision ID: 9f5b2a7d4c1e
Revises: 7b9f3c0b8d6c
Create Date: 2026-02-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f5b2a7d4c1e"
down_revision: Union[str, None] = "7b9f3c0b8d6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trip_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "trip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("phase", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('UTC', now())"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_trip_messages_trip_id",
        "trip_messages",
        ["trip_id"],
    )
    op.create_index(
        "idx_trip_messages_trip_id_created_at",
        "trip_messages",
        ["trip_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_trip_messages_trip_id_created_at", table_name="trip_messages")
    op.drop_index("idx_trip_messages_trip_id", table_name="trip_messages")
    op.drop_table("trip_messages")
