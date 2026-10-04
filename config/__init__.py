"""Project configuration helpers.

This module centralises feature flags used across the backend.  The new
flags allow tests and deployments to toggle advanced AI functionality
without touching service code.
"""

from __future__ import annotations

import os


# Master switch for all experimental/advanced AI features. Individual
# features may still be disabled even when this flag is True.
ENABLE_ADVANCED_AI: bool = os.getenv("ENABLE_ADVANCED_AI", "1") == "1"

# Feature specific AI flags.
ENABLE_TOUR_AI_MANAGER: bool = ENABLE_ADVANCED_AI and os.getenv(
    "ENABLE_TOUR_AI_MANAGER", "1"
) == "1"
ENABLE_PR_AI_MANAGER: bool = ENABLE_ADVANCED_AI and os.getenv(
    "ENABLE_PR_AI_MANAGER", "1"
) == "1"

# Luthiery is intentionally opt-in while the persistent character-owned
# crafting architecture is being introduced.
ENABLE_LUTHIERY_CRAFTING: bool = os.getenv("ENABLE_LUTHIERY_CRAFTING", "0") == "1"


__all__ = [
    "ENABLE_ADVANCED_AI",
    "ENABLE_TOUR_AI_MANAGER",
    "ENABLE_PR_AI_MANAGER",
    "ENABLE_LUTHIERY_CRAFTING",
]
