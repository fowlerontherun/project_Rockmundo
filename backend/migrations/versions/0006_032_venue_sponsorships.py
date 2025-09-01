from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '032_venue_sponsorships.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sponsor_ad_impressions;")
    op.execute("DROP TABLE IF EXISTS venue_sponsorships;")
