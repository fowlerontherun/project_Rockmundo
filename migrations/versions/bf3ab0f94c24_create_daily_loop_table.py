from alembic import op


# revision identifiers, used by Alembic.
revision = 'bf3ab0f94c24'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE daily_loop (
        user_id INTEGER PRIMARY KEY,
        login_streak INTEGER DEFAULT 0,
        last_login TEXT,
        current_challenge TEXT,
        challenge_progress INTEGER DEFAULT 0,
        reward_claimed INTEGER DEFAULT 0,
        catch_up_tokens INTEGER DEFAULT 0,
        challenge_tier INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE daily_loop")