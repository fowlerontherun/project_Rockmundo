"""Convenience re-exports for authentication utilities.

This module exposes helper functions for creating access tokens and verifying
user credentials by importing them from ``backend.utils.auth_utils``.
"""

from backend.utils.auth_utils import (
    create_access_token,
    verify_user_credentials,
)

__all__ = ["create_access_token", "verify_user_credentials"]
