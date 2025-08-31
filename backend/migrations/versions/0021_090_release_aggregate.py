from pathlib import Path
from alembic import op

revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '090_release_aggregate.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tracks;")
    op.execute("DROP TABLE IF EXISTS releases;")
