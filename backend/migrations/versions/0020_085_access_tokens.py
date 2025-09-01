from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '085_access_tokens.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS access_tokens;")
