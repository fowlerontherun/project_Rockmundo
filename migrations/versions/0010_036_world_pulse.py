from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '036_world_pulse.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split(';')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS genre_pulse_snapshots;")
