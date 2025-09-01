from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '034_media_publicity.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS media_effects;")
    op.execute("DROP TABLE IF EXISTS media_content;")
    op.execute("DROP TABLE IF EXISTS media_campaigns;")
    op.execute("DROP TABLE IF EXISTS media_outlets;")
