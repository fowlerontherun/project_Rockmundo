from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '035_media_moderation.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS media_moderation_logs;")
    op.execute("ALTER TABLE media_content DROP COLUMN mod_notes;")
    op.execute("ALTER TABLE media_content DROP COLUMN mod_status;")
    op.execute("ALTER TABLE media_campaigns DROP COLUMN mod_notes;")
    op.execute("ALTER TABLE media_campaigns DROP COLUMN mod_status;")
    op.execute("ALTER TABLE media_outlets DROP COLUMN mod_notes;")
    op.execute("ALTER TABLE media_outlets DROP COLUMN mod_status;")
