"""RBAC service with cached user role and permission lookups."""
from functools import lru_cache
from typing import Set

from auth.permissions import Permissions
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


@lru_cache(maxsize=1024)
def get_permissions_for_user(user_id: int) -> Set[str]:
    """Return the set of permission names assigned to ``user_id``."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.name FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id = ur.role_id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE ur.user_id = ?
            """,
            (user_id,),
        ).fetchall()
    return {row["name"] for row in rows}


def has_permission(user_id: int, permission: Permissions | str) -> bool:
    """Return ``True`` if ``user_id`` has ``permission``.

    ``permission`` may be provided as a :class:`Permissions` enum member or
    a raw string. Unknown permission strings raise ``ValueError`` to help
    catch typos at call sites.
    """
    perm_value = Permissions(permission).value if not isinstance(permission, Permissions) else permission.value
    return perm_value in get_permissions_for_user(user_id)


def clear_role_cache(user_id: int | None = None) -> None:
    """Invalidate cached RBAC lookups.

    ``functools.lru_cache`` does not provide a way to clear a single entry,
    so the entire cache is cleared. The ``user_id`` argument is accepted to
    make calling sites explicit about which user's roles changed.
    """
    get_roles_for_user.cache_clear()
    get_permissions_for_user.cache_clear()
