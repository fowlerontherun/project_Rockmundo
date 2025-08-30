"""Service logic for property management."""
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .achievement_service import AchievementService
from .economy_service import EconomyError, EconomyService

try:
    from .fame_service import FameService  # type: ignore
except Exception:  # pragma: no cover - fame service optional
    FameService = None  # type: ignore

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class PropertyError(Exception):
    pass


class PropertyService:
    def __init__(
        self,
        db_path: Optional[str] = None,
        economy: Optional[EconomyService] = None,
        fame: Optional[Any] = None,
        achievements: Optional[AchievementService] = None,
        weather: Optional[Any] = None,
    ) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)
        self.fame = fame
        self.achievements = achievements or AchievementService(self.db_path)
        self.weather = weather
        # ensure economy schema as well
        self.economy.ensure_schema()

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    purchase_price INTEGER NOT NULL,
                    base_rent INTEGER NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT
                )
                """
            )
            conn.commit()

    # ---------------- helpers ----------------
    def _fetch_property(self, property_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # ---------------- operations ----------------
    def buy_property(
        self,
        owner_id: int,
        name: str,
        property_type: str,
        location: str,
        price_cents: int,
        base_rent: int,
        mortgage_rate: float | None = None,
    ) -> int:
        if price_cents <= 0:
            raise PropertyError("Price must be positive")
        if mortgage_rate is not None:
            self.economy.create_loan(owner_id, price_cents, mortgage_rate, term_days=365)
        try:
            self.economy.withdraw(owner_id, price_cents)
        except EconomyError as e:
            raise PropertyError(str(e)) from e
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO properties (owner_id, name, type, location, purchase_price, base_rent)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (owner_id, name, property_type, location, price_cents, base_rent),
            )
            conn.commit()
            pid = int(cur.lastrowid or 0)
        try:
            self.achievements.grant(owner_id, "first_property")
        except Exception:
            pass
        return pid

    def list_properties(self, owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM properties"
            vals: List[Any] = []
            if owner_id is not None:
                q += " WHERE owner_id = ?"
                vals.append(owner_id)
            cur.execute(q, tuple(vals))
            return [dict(r) for r in cur.fetchall()]

    def upgrade_property(self, property_id: int, owner_id: int) -> Dict[str, Any]:
        prop = self._fetch_property(property_id)
        if not prop or prop["owner_id"] != owner_id:
            raise PropertyError("Property not found")
        new_level = prop["level"] + 1
        cost = int(prop["purchase_price"] * 0.5 * new_level)
        try:
            self.economy.withdraw(owner_id, cost)
        except EconomyError as e:
            raise PropertyError(str(e)) from e
        new_rent = int(prop["base_rent"] * 1.2)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE properties
                SET level = ?, base_rent = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (new_level, new_rent, property_id),
            )
            if cur.rowcount == 0:
                raise PropertyError("Upgrade failed")
            conn.commit()
        if self.fame:
            try:
                self.fame.award_fame(owner_id, "property_upgrade", new_level, f"Upgraded {prop['name']}")
            except Exception:
                pass
        return self._fetch_property(property_id) or {}

    def collect_rent(self, owner_id: int) -> int:
        props = self.list_properties(owner_id)
        total = 0
        for p in props:
            rent = p["base_rent"] * p["level"]
            if self.weather:
                forecast = self.weather.get_forecast(p["location"])
                if forecast.event and forecast.event.type == "storm":
                    rent = int(rent * 0.5)
                elif forecast.event and forecast.event.type == "festival":
                    rent = int(rent * 1.2)
            total += rent
        if total:
            self.economy.deposit(owner_id, total)
        return total

    def sell_property(self, property_id: int, owner_id: int) -> int:
        prop = self._fetch_property(property_id)
        if not prop or prop["owner_id"] != owner_id:
            raise PropertyError("Property not found")
        sale_price = int(prop["purchase_price"] * 0.8)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM properties WHERE id = ?", (property_id,))
            if cur.rowcount == 0:
                raise PropertyError("Sale failed")
            conn.commit()
        self.economy.deposit(owner_id, sale_price)
        return sale_price
