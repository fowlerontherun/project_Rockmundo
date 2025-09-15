"""Generate the OpenAPI schema for the FastAPI application.

The script is used in CI to ensure that the application and its route
definitions produce a valid OpenAPI specification.  It writes the schema
to ``openapi.json`` in the repository root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Ensure project root is on the import path so that modules like ``auth`` can be
# imported when this script is executed directly.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from api import app  # noqa: E402  (import after path manipulation)


def main() -> None:
    schema = app.openapi()
    out_path = Path("openapi.json")
    out_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI schema → {out_path}")


if __name__ == "__main__":  # pragma: no cover - utility script
    main()

