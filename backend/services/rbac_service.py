"""RBAC service with cached user role lookups."""
from functools import lru_cache
from typing import Set

from utils.db import get_conn


@lru_cache(maxsize=1024)
def get_roles_for_user(user_id: int) -> Set[str]:
    """Return the set of role names assigned to ``user_id``."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT r.name FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = ?
            """,
            (user_id,),
        ).fetchall()
    return {row["name"] for row in rows}

def clear_role_cache(user_id: int | None = None) -> None:
    """Invalidate cached role lookups.

    ``functools.lru_cache`` does not provide a way to clear a single entry,
    so the entire cache is cleared. The ``user_id`` argument is accepted to
    make calling sites explicit about which user's roles changed.
    """
    get_roles_for_user.cache_clear()
