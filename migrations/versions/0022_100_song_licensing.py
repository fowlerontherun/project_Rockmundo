from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '100_add_song_licensing.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS cover_royalties;')
    # SQLite does not support dropping columns easily; omit rollback for column additions
