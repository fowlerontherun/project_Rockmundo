from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '060_music_sales_streams.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS music_ledger_view;")
    op.execute("DROP TABLE IF EXISTS streams;")
    op.execute("DROP TABLE IF EXISTS sales_vinyl;")
    op.execute("DROP TABLE IF EXISTS sales_digital;")
    op.execute("DROP TABLE IF EXISTS songs;")
    op.execute("DROP TABLE IF EXISTS albums;")
