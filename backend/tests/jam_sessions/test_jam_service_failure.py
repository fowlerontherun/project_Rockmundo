import logging
import pytest

from services.jam_service import JamService
from services.economy_service import EconomyService


class FailingEconomy(EconomyService):
    def ensure_schema(self) -> None:  # type: ignore[override]
        raise ValueError("boom")


def test_jam_service_init_raises_and_logs(caplog):
    econ = FailingEconomy()
    with caplog.at_level(logging.ERROR), pytest.raises(
        RuntimeError, match="failed to ensure economy schema: boom"
    ):
        JamService(economy=econ)
    assert "Failed to ensure economy schema" in caplog.text
