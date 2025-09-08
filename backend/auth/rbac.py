"""Central RBAC service coordinating user roles and permissions."""
from __future__ import annotations

from functools import lru_cache
from typing import Set

from auth.permissions import Permissions
from utils.db import get_conn


class RBACService:
    """Service providing role and permission lookups with caching."""

    @lru_cache(maxsize=1024)
    def get_roles_for_user(self, user_id: int) -> Set[str]:
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
    def get_permissions_for_user(self, user_id: int) -> Set[str]:
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

    def has_permission(self, user_id: int, permission: Permissions | str) -> bool:
        """Return ``True`` if ``user_id`` has ``permission``."""
        perm_value = (
            Permissions(permission).value
            if not isinstance(permission, Permissions)
            else permission.value
        )
        return perm_value in self.get_permissions_for_user(user_id)

    def clear_cache(self) -> None:
        """Invalidate cached lookups."""
        self.get_roles_for_user.cache_clear()
        self.get_permissions_for_user.cache_clear()


rbac_service = RBACService()
