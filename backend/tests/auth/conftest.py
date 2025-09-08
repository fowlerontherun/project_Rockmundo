from importlib import metadata as importlib_metadata
import sys
import types

# Stub out optional dependency used by pydantic's EmailStr to avoid requiring
# the external ``email_validator`` package during tests.
email_validator = types.ModuleType("email_validator")
email_validator.validate_email = lambda *a, **k: None
email_validator.EmailNotValidError = Exception
sys.modules.setdefault("email_validator", email_validator)


_real_version = importlib_metadata.version


def _fake_version(name: str) -> str:
    if name == "email-validator":
        return "2.0.0"
    return _real_version(name)


importlib_metadata.version = _fake_version  # type: ignore[attr-defined]
