"""Admin utilities for XP management."""

from __future__ import annotations

from pathlib import Path

from models.xp_config import (
    XPConfig,
    get_config,
    set_config,
    save_config,
)


class XPAdminService:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "xp_config.json"

    def get_config(self) -> XPConfig:
        return get_config()

    def update_config(self, **changes) -> XPConfig:
        cfg = get_config()
        for k, v in changes.items():
            if hasattr(cfg, k) and v is not None:
                setattr(cfg, k, v)
        set_config(cfg)
        save_config(cfg, self.config_path)
        return cfg
