import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

import core.config as config_module
import backend.services.storage_service as storage_service

import os
from importlib import reload

def test_get_storage_backend_creates_attachment_dir(tmp_path):
    reload(config_module)
    config_module.settings.storage.local_root = str(tmp_path / "storage")
    reload(storage_service)
    storage = storage_service.get_storage_backend()
    os.makedirs(os.path.join(storage.root, "mail", "attachments"), exist_ok=True)
    assert (tmp_path / "storage" / "mail" / "attachments").is_dir()
