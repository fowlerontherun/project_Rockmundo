from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '050_tours_and_venues.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tour_stops;")
    op.execute("DROP TABLE IF EXISTS tours;")
    op.execute("DROP TABLE IF EXISTS venues;")
