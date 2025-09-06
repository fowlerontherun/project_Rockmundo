from pathlib import Path
from alembic import op

revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '105_chart_regions.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_charts_region;")
    # SQLite does not support dropping columns easily; omit column removal
