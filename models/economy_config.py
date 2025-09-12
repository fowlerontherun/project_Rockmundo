from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

# Default location for persisted config
CONFIG_PATH = Path(__file__).resolve().parents[1] / "economy_config.json"


@dataclass
class EconomyConfig:
    """Runtime tunable economy settings."""

    tax_rate: float = 0.0
    inflation_rate: float = 0.0
    payout_rate: int = 100  # base payout amount in cents


def load_config(path: Path = CONFIG_PATH) -> EconomyConfig:
    if path.exists():
        data = json.loads(path.read_text())
        return EconomyConfig(**data)
    return EconomyConfig()


def save_config(config: EconomyConfig, path: Path = CONFIG_PATH) -> None:
    path.write_text(json.dumps(asdict(config)))


# In-memory singleton used by services
_config: EconomyConfig = load_config()


def get_config() -> EconomyConfig:
    return _config


def set_config(config: EconomyConfig) -> None:
    global _config
    _config = config
