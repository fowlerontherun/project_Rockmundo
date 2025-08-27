"""Minimal locale utilities.

This module provides a lightweight translation helper that reads ``.po`` files
directly.  Compiled ``.mo`` catalogs are intentionally omitted from the
repository, so translations are parsed at runtime and cached per locale.
"""

from contextvars import ContextVar
from pathlib import Path
from typing import Dict

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "en"

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)
_translations: Dict[str, Dict[str, str]] = {}


def set_locale(locale: str) -> None:
    """Set the active locale for the current request."""

    _current_locale.set(locale)


def _load_translations(locale: str) -> Dict[str, str]:
    """Load translations from a ``.po`` file for *locale*.

    Only the simple ``msgid``/``msgstr`` pairs are supported which is
    sufficient for the project's small catalogs.
    """

    catalog: Dict[str, str] = {}
    po_path = LOCALES_DIR / locale / "LC_MESSAGES" / "messages.po"
    with po_path.open("r", encoding="utf-8") as f:  # noqa: PTH123
        msgid: str | None = None
        for raw_line in f:
            line = raw_line.strip()
            if line.startswith("msgid "):
                msgid = line[6:].strip().strip("\"")
            elif line.startswith("msgstr ") and msgid is not None:
                msgstr = line[7:].strip().strip("\"")
                if msgid:
                    catalog[msgid] = msgstr
                msgid = None
    return catalog


def gettext_(message: str) -> str:
    """Translate ``message`` for the current locale."""

    locale = _current_locale.get()
    if locale not in _translations:
        try:
            _translations[locale] = _load_translations(locale)
        except FileNotFoundError:
            _translations[locale] = _load_translations(DEFAULT_LOCALE)
    return _translations[locale].get(message, message)


_ = gettext_

