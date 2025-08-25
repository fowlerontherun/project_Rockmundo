# File: backend/core/config.py
import os
from pathlib import Path
from typing import Optional

def _load_dotenv(dotenv_path: Optional[str] = None) -> None:
    path = dotenv_path or (Path(__file__).resolve().parents[2] / ".env")
    try:
        if Path(path).exists():
            for line in Path(path).read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

_load_dotenv()

class Settings:
    DB_PATH: str = os.getenv("ROCKMUNDO_DB_PATH", str((Path(__file__).resolve().parents[1] / "rockmundo.db")))
    ENV: str = os.getenv("ROCKMUNDO_ENV", "dev")
    LOG_LEVEL: str = os.getenv("ROCKMUNDO_LOG_LEVEL", "INFO")
    # Auth
    JWT_SECRET: str = os.getenv("ROCKMUNDO_JWT_SECRET", "dev-change-me")
    JWT_ISS: str = os.getenv("ROCKMUNDO_JWT_ISS", "rockmundo")
    JWT_AUD: str = os.getenv("ROCKMUNDO_JWT_AUD", "rockmundo-app")
    ACCESS_TOKEN_TTL_MIN: int = int(os.getenv("ROCKMUNDO_ACCESS_TTL_MIN", "30"))
    REFRESH_TOKEN_TTL_DAYS: int = int(os.getenv("ROCKMUNDO_REFRESH_TTL_DAYS", "30"))

settings = Settings()
