from pathlib import Path
from alembic import op

revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '165_chart_country_code.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_charts_country;")
    # SQLite does not support dropping columns
