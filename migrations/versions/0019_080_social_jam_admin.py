from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '080_social_jam_admin.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS jam_streams;")
    op.execute("DROP TABLE IF EXISTS jam_sessions;")
    op.execute("DROP TABLE IF EXISTS friendships;")
    op.execute("DROP TABLE IF EXISTS friend_requests;")
    op.execute("DROP TABLE IF EXISTS admin_audit;")
