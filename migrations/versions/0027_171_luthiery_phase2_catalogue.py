from pathlib import Path
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "171_luthiery_phase2_catalogue.sql"


def upgrade() -> None:
    for statement in SQL_FILE.read_text().split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    for table in (
        "material_purchase_history",
        "luthier_supplier_stock",
        "character_crafting_materials",
        "crafting_unlocks",
        "instrument_shapes",
        "crafting_component_designs",
        "crafting_materials",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
