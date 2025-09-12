"""Time-series forecasting for song popularity."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.database import DB_PATH

try:
    from statsmodels.tsa.arima.model import ARIMA  # type: ignore
except Exception:  # pragma: no cover - fallback if library missing
    ARIMA = None  # type: ignore


def _ensure_schema(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_popularity_forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            forecast_date TEXT NOT NULL,
            predicted_score REAL NOT NULL,
            lower REAL,
            upper REAL,
            created_at TEXT NOT NULL
        )
        """
    )


class SongPopularityForecastService:
    """Generate simple ARIMA-based forecasts for song popularity."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH

    def forecast_song(self, song_id: int, days: int = 7) -> List[Dict]:
        """Recompute forecasts for a song and store them."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            cur.execute(
                "SELECT popularity_score, updated_at FROM song_popularity WHERE song_id=? ORDER BY updated_at",
                (song_id,),
            )
            rows = cur.fetchall()
            if len(rows) < 2:
                return []
            scores = [r[0] for r in rows]
            if ARIMA is not None:
                try:
                    model = ARIMA(scores, order=(1, 1, 0))
                    model_fit = model.fit()
                    forecast = model_fit.get_forecast(steps=days)
                    preds = forecast.predicted_mean.tolist()
                    conf = forecast.conf_int(alpha=0.05).to_numpy().tolist()
                except Exception:
                    preds = [scores[-1]] * days
                    conf = [[scores[-1], scores[-1]] for _ in range(days)]
            else:  # simple persistence forecast
                preds = [scores[-1]] * days
                conf = [[scores[-1], scores[-1]] for _ in range(days)]
            last_date = datetime.fromisoformat(rows[-1][1])
            cur.execute(
                "DELETE FROM song_popularity_forecasts WHERE song_id=?",
                (song_id,),
            )
            results: List[Dict] = []
            for idx in range(days):
                date = (last_date + timedelta(days=idx + 1)).isoformat()
                pred = float(preds[idx])
                lower = float(conf[idx][0])
                upper = float(conf[idx][1])
                now = datetime.utcnow().isoformat()
                cur.execute(
                    """
                    INSERT INTO song_popularity_forecasts
                        (song_id, forecast_date, predicted_score, lower, upper, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (song_id, date, pred, lower, upper, now),
                )
                results.append(
                    {
                        "forecast_date": date,
                        "predicted_score": pred,
                        "confidence_interval": [lower, upper],
                    }
                )
            conn.commit()
            return results

    def get_forecast(self, song_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            cur.execute(
                """
                SELECT forecast_date, predicted_score, lower, upper
                FROM song_popularity_forecasts
                WHERE song_id=? ORDER BY forecast_date
                """,
                (song_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "forecast_date": r[0],
                    "predicted_score": r[1],
                    "confidence_interval": [r[2], r[3]],
                }
                for r in rows
            ]

    def recompute_all(self) -> int:
        """Recompute forecasts for all songs with history."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT song_id FROM song_popularity")
            ids = [r[0] for r in cur.fetchall()]
        count = 0
        for sid in ids:
            if self.forecast_song(sid):
                count += 1
        return count


forecast_service = SongPopularityForecastService()


def _schedule_forecast_recompute() -> None:
    """Schedule nightly recomputation of all song forecasts."""
    try:  # best effort; scheduler may not be set up in all environments
        from backend.services.scheduler_service import schedule_task

        run_at = (datetime.utcnow() + timedelta(days=1)).isoformat()
        schedule_task(
            "song_popularity_forecast",
            {},
            run_at,
            recurring=True,
            interval_days=1,
        )
    except Exception:
        pass


# Attempt to schedule on import
_schedule_forecast_recompute()
