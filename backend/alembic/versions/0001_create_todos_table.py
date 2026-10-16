"""create todos table

Revision ID: 0001_create_todos
Revises:
Create Date: 2026-10-16 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_todos"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "priority",
            sa.Enum("LOW", "MEDIUM", "HIGH", name="todopriority", native_enum=False, length=20),
            nullable=False,
            server_default="MEDIUM",
        ),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="General"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_todos_id", "todos", ["id"])
    op.create_index("ix_todos_completed", "todos", ["completed"])
    op.create_index("ix_todos_category", "todos", ["category"])


def downgrade() -> None:
    op.drop_index("ix_todos_category", table_name="todos")
    op.drop_index("ix_todos_completed", table_name="todos")
    op.drop_index("ix_todos_id", table_name="todos")
    op.drop_table("todos")
