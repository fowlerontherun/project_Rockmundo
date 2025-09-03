from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '045_mail_attachments_and_fts.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS mail_messages_ai;")
    op.execute("DROP TRIGGER IF EXISTS mail_messages_ad;")
    op.execute("DROP TABLE IF EXISTS mail_fts;")
    op.execute("DROP TABLE IF EXISTS mail_attachments;")
