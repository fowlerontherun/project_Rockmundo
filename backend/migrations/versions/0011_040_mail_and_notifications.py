from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '040_mail_and_notifications.sql'

def upgrade() -> None:
    op.execute(SQL_FILE.read_text())

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notifications;")
    op.execute("DROP TABLE IF EXISTS mail_participants;")
    op.execute("DROP TABLE IF EXISTS mail_messages;")
    op.execute("DROP TABLE IF EXISTS mail_threads;")
