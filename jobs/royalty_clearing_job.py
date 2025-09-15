"""Periodic job for settling cover royalties.

This job aggregates outstanding cover royalty transactions and marks them as
paid.  Earnings are distributed to rights holders based on the ``royalties``
split of the original song.  For simplicity the job only updates the
``cover_royalties`` table and prints distributions; integrating with a real
payment system is outside the scope of this module.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable, Tuple

from database import DB_PATH


def _fetch_outstanding(cur: sqlite3.Cursor) -> Iterable[Tuple[int, int, int, int]]:
    """Yield outstanding cover royalty rows as ``(id, song_id, cover_band_id, owed)``."""

    cur.execute(
        """
        SELECT id, song_id, cover_band_id, amount_owed
        FROM cover_royalties
        WHERE amount_owed > amount_paid
        """
    )
    return cur.fetchall()


def run(db: str = DB_PATH) -> None:
    """Run the royalty clearing process for the given database."""

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    rows = _fetch_outstanding(cur)
    for row in rows:
        rid, song_id, cover_band_id, owed = row
        cur.execute(
            "SELECT user_id, percent FROM royalties WHERE song_id = ?", (song_id,)
        )
        splits = cur.fetchall()
        for user_id, percent in splits:
            amount = owed * percent // 100
            print(
                f"Settled {amount}¢ to rights holder {user_id} from band {cover_band_id} cover of song {song_id}"
            )
        cur.execute(
            "UPDATE cover_royalties SET amount_paid = amount_owed WHERE id = ?",
            (rid,),
        )
    conn.commit()
    conn.close()
