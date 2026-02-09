"""Add user_type to users table

Revision ID: 7b9f3c0b8d6c
Revises: 2d5f38b0a881
Create Date: 2026-02-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7b9f3c0b8d6c"
down_revision = "2d5f38b0a881"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "user_type",
            sa.String(length=50),
            nullable=False,
            server_default="free",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "user_type")
