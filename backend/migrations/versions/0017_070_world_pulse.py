from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '070_world_pulse.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS world_pulse_weekly_cache;")
    op.execute("DROP TABLE IF EXISTS world_pulse_rankings;")
    op.execute("DROP TABLE IF EXISTS world_pulse_metrics;")
    op.execute("DROP TABLE IF EXISTS app_config;")
    op.execute("DROP TABLE IF EXISTS job_metadata;")
