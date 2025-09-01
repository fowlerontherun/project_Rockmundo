"""Minimal ``pydantic.types`` for tests."""

class SecretStr(str):
    pass

class SecretBytes(bytes):
    pass

__all__ = ["SecretStr", "SecretBytes"]
