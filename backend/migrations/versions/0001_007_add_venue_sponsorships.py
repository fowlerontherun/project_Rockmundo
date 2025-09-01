from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '007_add_venue_sponsorships.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_current_venue_sponsorship;")
    op.execute("DROP TABLE IF EXISTS sponsorship_ad_events;")
    op.execute("DROP TABLE IF EXISTS venue_sponsorships;")
    op.execute("DROP TABLE IF EXISTS sponsors;")
