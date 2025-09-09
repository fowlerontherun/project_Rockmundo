"""Tests for chemistry service initialization logging."""

# ruff: noqa: E402,I001
import logging
import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "backend")])

from backend.services import chemistry_service
from backend.services.chemistry_service import ChemistryService
from backend.models.player_chemistry import Base

def test_init_logs_and_raises_on_metadata_creation_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    chemistry_service.DB_PATH.unlink(missing_ok=True)

    def failing_create_all(*args, **kwargs):
        raise SQLAlchemyError("boom")

    monkeypatch.setattr(Base.metadata, "create_all", failing_create_all)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(SQLAlchemyError, match="boom"):
            ChemistryService()

    assert "Failed to initialize ChemistryService database" in caplog.text
    chemistry_service.DB_PATH.unlink(missing_ok=True)
