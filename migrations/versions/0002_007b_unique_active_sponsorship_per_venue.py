from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '007b_unique_active_sponsorship_per_venue.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_current_sponsor_per_venue;")
