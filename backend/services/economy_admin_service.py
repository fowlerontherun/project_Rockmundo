"""Admin utilities for economy management."""

from __future__ import annotations

from pathlib import Path
from typing import List

from backend.models.economy_config import (
    EconomyConfig,
    get_config,
    set_config,
    save_config,
)
from backend.services.economy_service import EconomyService, TransactionRecord


class EconomyAdminService:
    def __init__(
        self,
        config_path: Path | None = None,
        economy_service: EconomyService | None = None,
    ) -> None:
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "economy_config.json"
        self.economy_service = economy_service or EconomyService()

    # -------- config management --------
    def get_config(self) -> EconomyConfig:
        return get_config()

    def update_config(self, **changes) -> EconomyConfig:
        cfg = get_config()
        for k, v in changes.items():
            if hasattr(cfg, k) and v is not None:
                setattr(cfg, k, v)
        set_config(cfg)
        save_config(cfg, self.config_path)
        return cfg

    # -------- ledger queries --------
    def recent_transactions(self, limit: int = 50) -> List[TransactionRecord]:
        return self.economy_service.list_recent_transactions(limit=limit)
