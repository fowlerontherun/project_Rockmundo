"""Alembic wrapper for Luthiery Phase 4 persistent crafting."""
from pathlib import Path
from alembic import op

revision = "0028_172"
down_revision = "0027_171"
branch_labels = None
depends_on = None
SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "172_luthiery_phase4_crafting.sql"

def upgrade() -> None:
    conn = op.get_bind()
    for statement in SQL_FILE.read_text().split(";"):
        if statement.strip():
            conn.exec_driver_sql(statement)

def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("DROP TABLE IF EXISTS crafting_jobs")
    conn.exec_driver_sql("DROP TABLE IF EXISTS crafted_item_parts")
    conn.exec_driver_sql("DROP TABLE IF EXISTS crafted_items")
