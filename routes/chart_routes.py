import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user_id
from database import DB_PATH
from services.chart_service import calculate_weekly_chart, get_chart

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/regions/breakdown")
def charts_region_breakdown(chart_type: str = "streams_song", period: str = "daily"):
    """Return latest chart entry counts per region."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT region, MAX(period_start) AS latest
            FROM chart_snapshots
            WHERE chart_type = ? AND period = ?
            GROUP BY region
            """,
            (chart_type, period),
        )
        rows = cur.fetchall()
        out = {}
        for region, latest in rows:
            cur.execute(
                """
                SELECT COUNT(*) FROM chart_snapshots
                WHERE chart_type = ? AND period = ? AND region = ? AND period_start = ?
                """,
                (chart_type, period, region, latest),
            )
            out[region] = int(cur.fetchone()[0] or 0)
    return out


@router.get("/{country}")
def get_country_charts(country: str, chart_type: str = "streams_song", period: str = "daily"):
    """Return latest chart snapshot for a given ``country``."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MAX(period_start)
            FROM chart_snapshots
            WHERE chart_type = ? AND period = ? AND country_code = ?
            """,
            (chart_type, period, country.upper()),
        )
        row = cur.fetchone()
        if not row or row[0] is None:
            return []
        latest = row[0]
        cur.execute(
            """
            SELECT rank, work_type, work_id, band_id, title, metric_value
            FROM chart_snapshots
            WHERE chart_type = ? AND period = ? AND country_code = ? AND period_start = ?
            ORDER BY rank ASC
            """,
            (chart_type, period, country.upper(), latest),
        )
        rows = cur.fetchall()
    return [
        {
            "rank": rank,
            "work_type": work_type,
            "work_id": work_id,
            "band_id": band_id,
            "title": title,
            "metric": metric,
        }
        for rank, work_type, work_id, band_id, title, metric in rows
    ]


@router.get("/country/{country}/{week_start}")
def get_country_chart(
    country: str,
    week_start: str,
    _req: Request,
    user_id: int = Depends(get_current_user_id),
):
    """Retrieve weekly chart entries for a specific country."""
    return get_chart("Global Top 100", country.upper(), week_start)


@router.get("/{region}/{week_start}")
def get_global_chart(
    region: str,
    week_start: str,
    _req: Request,
    user_id: int = Depends(get_current_user_id),
):
    return get_chart("Global Top 100", region, week_start)


@router.post("/{region}/recalculate", status_code=204)
def recalculate_charts(
    region: str, _req: Request, user_id: int = Depends(get_current_user_id)
):
    try:
        calculate_weekly_chart(region=region)
    except Exception as e:  # pragma: no cover - example stub
        raise HTTPException(status_code=500, detail=str(e))
