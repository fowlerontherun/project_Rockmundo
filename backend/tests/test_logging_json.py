import json
import logging

from backend.utils.logging import setup_logging


def test_json_logging_format(capfd):
    setup_logging()
    logging.getLogger().info("hello world")
    err = capfd.readouterr().err.strip().splitlines()[-1]
    data = json.loads(err)
    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
