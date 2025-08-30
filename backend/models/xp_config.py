from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

# Default location for persisted config
CONFIG_PATH = Path(__file__).resolve().parents[1] / "xp_config.json"


@dataclass
class XPConfig:
    """Runtime tunable experience settings."""

    daily_cap: int = 0
    new_player_multiplier: float = 1.0
    rested_xp_rate: float = 1.0


def load_config(path: Path = CONFIG_PATH) -> XPConfig:
    if path.exists():
        data = json.loads(path.read_text())
        return XPConfig(**data)
    return XPConfig()


def save_config(config: XPConfig, path: Path = CONFIG_PATH) -> None:
    path.write_text(json.dumps(asdict(config)))


# In-memory singleton used by services
_config: XPConfig = load_config()


def get_config() -> XPConfig:
    return _config


def set_config(config: XPConfig) -> None:
    global _config
    _config = config
