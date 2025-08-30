"""Minimal locale utilities.

This module now leverages compiled ``.mo`` catalogs for fast startup while still
falling back to parsing ``.po`` sources if necessary.  Plural forms and message
contexts are supported via :class:`gettext.GNUTranslations`.
"""

from __future__ import annotations

import gettext
import subprocess
from contextvars import ContextVar
from pathlib import Path
from typing import Dict

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "en"

# discover available locales at import time so the API can expose them
SUPPORTED_LOCALES = sorted(
    p.name for p in LOCALES_DIR.iterdir() if (p / "LC_MESSAGES" / "messages.po").exists()
)

_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)
_translations: Dict[str, gettext.NullTranslations] = {}


def set_locale(locale: str) -> None:
    """Set the active locale for the current request."""

    _current_locale.set(locale)


def _load_translations(locale: str) -> gettext.NullTranslations:
    """Load translations for *locale*.

    If a compiled ``.mo`` catalog is present it is used directly.  Otherwise the
    corresponding ``.po`` file is compiled on the fly using ``msgfmt``.
    """

    locale_dir = LOCALES_DIR / locale / "LC_MESSAGES"
    mo_path = locale_dir / "messages.mo"
    po_path = locale_dir / "messages.po"

    if not mo_path.exists():
        # Generate the compiled catalog; ``msgfmt`` is widely available and
        # avoids a heavy runtime dependency such as ``polib``.
        subprocess.run(["msgfmt", str(po_path), "-o", str(mo_path)], check=True)

    with mo_path.open("rb") as fp:  # noqa: PTH123
        return gettext.GNUTranslations(fp)


def _get_translations() -> gettext.NullTranslations:
    locale = _current_locale.get()
    if locale not in _translations:
        try:
            _translations[locale] = _load_translations(locale)
        except FileNotFoundError:
            _translations[locale] = _load_translations(DEFAULT_LOCALE)
    return _translations[locale]


def gettext_(message: str) -> str:
    """Translate ``message`` for the current locale."""

    return _get_translations().gettext(message)


def ngettext_(singular: str, plural: str, n: int) -> str:
    """Return the pluralized translation for ``n``."""

    return _get_translations().ngettext(singular, plural, n)


def pgettext_(context: str, message: str) -> str:
    """Return the translation for ``message`` in ``context``."""

    return _get_translations().pgettext(context, message)


def npgettext_(context: str, singular: str, plural: str, n: int) -> str:
    """Return the pluralized translation within ``context``."""

    return _get_translations().npgettext(context, singular, plural, n)


_ = gettext_

__all__ = [
    "_",
    "gettext_",
    "ngettext_",
    "pgettext_",
    "npgettext_",
    "set_locale",
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
]

