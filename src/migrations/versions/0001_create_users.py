"""create users_schema and users table

Revision ID: 0001
Revises:
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "users_schema"


def upgrade() -> None:
    # Используем чистый SQL с IF NOT EXISTS — полностью идемпотентно
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS users_schema"))

    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS users_schema.users (
            id          SERIAL       NOT NULL,
            uid         UUID         NOT NULL,
            name        VARCHAR(120) NOT NULL,
            surname     VARCHAR(120) NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT pk_users    PRIMARY KEY (id),
            CONSTRAINT uq_users_uid UNIQUE (uid)
        )
    """))

    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_users_id  ON users_schema.users (id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_users_uid ON users_schema.users (uid)"
    ))


def downgrade() -> None:
    op.drop_index("ix_users_uid", table_name="users", schema=SCHEMA)
    op.drop_index("ix_users_id", table_name="users", schema=SCHEMA)
    op.drop_table("users", schema=SCHEMA)
    op.execute(sa.schema.DropSchema(SCHEMA, cascade=True))

