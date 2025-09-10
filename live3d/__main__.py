"""Command line entry point for the live3d prototype."""

from __future__ import annotations

import argparse

from .engine import render_gig


def main() -> None:
    parser = argparse.ArgumentParser(description="Render gig data in 3D")
    parser.add_argument("--gig-id", type=int, required=True, help="Gig identifier")
    parser.add_argument(
        "--db", default="rockmundo.db", help="Path to gig SQLite database"
    )
    args = parser.parse_args()
    render_gig(args.gig_id, args.db)


if __name__ == "__main__":
    main()
