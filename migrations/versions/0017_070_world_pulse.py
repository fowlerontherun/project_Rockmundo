from pathlib import Path
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '070_world_pulse.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

    app_config_table = sa.table(
        'app_config',
        sa.column('key', sa.String),
        sa.column('value', sa.String)
    )

    op.bulk_insert(app_config_table, [
        {
            'key': 'world_pulse_weights',
            'value': '{"streams":1.0,"digital":10.0,"vinyl":15.0}'
        }
    ])

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS world_pulse_weekly_cache;")
    op.execute("DROP TABLE IF EXISTS world_pulse_rankings;")
    op.execute("DROP TABLE IF EXISTS world_pulse_metrics;")
    op.execute("DROP TABLE IF EXISTS app_config;")
    op.execute("DROP TABLE IF EXISTS job_metadata;")
