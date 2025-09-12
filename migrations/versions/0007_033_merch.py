from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '033_merch.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split(';')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS merch_refunds;")
    op.execute("DROP TABLE IF EXISTS merch_order_items;")
    op.execute("DROP TABLE IF EXISTS merch_orders;")
    op.execute("DROP TABLE IF EXISTS merch_skus;")
    op.execute("DROP TABLE IF EXISTS merch_products;")
