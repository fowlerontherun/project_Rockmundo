import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


def make_storage(monkeypatch):
    dummy_client = types.SimpleNamespace()
    monkeypatch.setitem(
        sys.modules,
        "boto3",
        types.SimpleNamespace(client=lambda *a, **k: dummy_client),
    )

    class DummyConfig:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setitem(
        sys.modules,
        "botocore.client",
        types.SimpleNamespace(Config=DummyConfig),
    )

    class DummyClientError(Exception):
        def __init__(self, response, operation_name):
            self.response = response
            self.operation_name = operation_name

    monkeypatch.setitem(
        sys.modules,
        "botocore.exceptions",
        types.SimpleNamespace(ClientError=DummyClientError),
    )

    s3_module = importlib.import_module("backend.storage.s3")
    importlib.reload(s3_module)
    storage = s3_module.S3Storage("bucket", "region")
    return storage, dummy_client, DummyClientError


def test_exists_returns_false_for_missing_key(monkeypatch):
    storage, client, ClientError = make_storage(monkeypatch)

    def head_object(**kwargs):
        raise ClientError({"Error": {"Code": "404"}}, "head_object")

    client.head_object = head_object
    assert storage.exists("missing") is False


def test_exists_raises_unexpected_client_error(monkeypatch):
    storage, client, ClientError = make_storage(monkeypatch)

    def head_object(**kwargs):
        raise ClientError({"Error": {"Code": "500"}}, "head_object")

    client.head_object = head_object
    with pytest.raises(ClientError):
        storage.exists("other")


def test_exists_raises_other_exceptions(monkeypatch):
    storage, client, _ = make_storage(monkeypatch)

    def head_object(**kwargs):
        raise RuntimeError("boom")

    client.head_object = head_object
    with pytest.raises(RuntimeError):
        storage.exists("key")

