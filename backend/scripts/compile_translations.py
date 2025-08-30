"""Compile translation catalogs.

Run during builds or CI to generate ``.mo`` files from the source ``.po``
messages. Using compiled catalogs significantly speeds up application start.
"""

from pathlib import Path
import subprocess


LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"


def main() -> None:
    for locale_dir in LOCALES_DIR.iterdir():
        po_path = locale_dir / "LC_MESSAGES" / "messages.po"
        mo_path = locale_dir / "LC_MESSAGES" / "messages.mo"
        if po_path.exists():
            mo_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["msgfmt", str(po_path), "-o", str(mo_path)], check=True)


if __name__ == "__main__":
    main()

