from pathlib import Path
from alembic import op

# revision identifiers, used by Alembic.
revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None

SQL_FILE = Path(__file__).resolve().parent.parent / 'sql' / '150_permissions.sql'

def upgrade() -> None:
    statements = SQL_FILE.read_text().split('-- SPLIT --')
    for statement in statements:
        if statement.strip():
            op.execute(statement)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS role_permissions;")
    op.execute("DROP TABLE IF EXISTS permissions;")
