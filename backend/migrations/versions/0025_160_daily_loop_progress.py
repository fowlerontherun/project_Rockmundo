from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '160_daily_loop_progress.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())


def downgrade() -> None:
    op.execute("ALTER TABLE daily_loop DROP COLUMN tier_progress;")
    op.execute("ALTER TABLE daily_loop DROP COLUMN weekly_goal_count;")
