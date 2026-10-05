"""Persistent Luthiery Phase 2 catalogue and supplier service."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from services.luthiery_progression import UNLOCKS
from services.luthiery_visual_definitions import SHAPES as VISUAL_SHAPES, visual_definition

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

MATERIALS = (
    ("luthier.material.basswood", "Basswood", "body_wood", "common", 4500, 0.92, {"tone": 1, "playability": 1}, 1),
    ("luthier.material.poplar", "Poplar", "body_wood", "common", 4000, 0.90, {"playability": 1}, 1),
    ("luthier.material.maple", "Maple", "wood", "common", 6000, 1.00, {"clarity": 2, "sustain": 1}, 10),
    ("luthier.material.rosewood", "Rosewood", "fretboard_wood", "uncommon", 7500, 1.04, {"tone": 2}, 20),
    ("luthier.material.alder", "Alder", "body_wood", "uncommon", 7000, 1.03, {"tone": 2, "clarity": 1}, 30),
    ("luthier.material.ash", "Ash", "body_wood", "uncommon", 8000, 1.05, {"clarity": 2, "sustain": 1}, 40),
    ("luthier.material.mahogany", "Mahogany", "wood", "rare", 10500, 1.09, {"tone": 3, "sustain": 2}, 50),
    ("luthier.material.walnut", "Walnut", "wood", "rare", 11500, 1.10, {"tone": 2, "reliability": 1}, 60),
    ("luthier.material.ebony", "Ebony", "fretboard_wood", "rare", 13500, 1.12, {"clarity": 3, "playability": 2}, 70),
    ("luthier.material.flame_maple", "Flame Maple", "decorative_wood", "epic", 17500, 1.15, {"stage_impact": 3, "clarity": 1}, 80),
    ("luthier.material.quilted_maple", "Quilted Maple", "decorative_wood", "epic", 19500, 1.17, {"stage_impact": 4}, 90),
    ("luthier.material.premium_exotic", "Premium Exotic Wood", "wood", "legendary", 30000, 1.22, {"tone": 3, "stage_impact": 4}, 100),
)

COMPONENTS = (
    ("luthier.component.body.standard", "Standard Body Blank", "body", 1, 3000),
    ("luthier.component.neck.bolt_on", "Bolt-On Neck", "neck", 1, 3500),
    ("luthier.component.neck.set", "Set Neck", "neck", 50, 7500),
    ("luthier.component.fretboard.standard", "Standard Fretboard", "fretboard", 1, 2500),
    ("luthier.component.fretboard.precision", "Precision Fretboard", "fretboard", 60, 6500),
    ("luthier.component.electronics.ceramic", "Ceramic Electronics", "electronics", 1, 4000),
    ("luthier.component.electronics.single_coil", "Standard Single-Coil", "electronics", 20, 5000),
    ("luthier.component.electronics.humbucker", "Standard Humbucker", "electronics", 30, 6000),
    ("luthier.component.electronics.p_bass", "P-Style Bass Pickup", "electronics", 20, 5500),
    ("luthier.component.electronics.j_bass", "J-Style Bass Pickup", "electronics", 30, 6000),
    ("luthier.component.electronics.alnico", "Alnico Electronics", "electronics", 40, 8000),
    ("luthier.component.electronics.active", "Active Electronics", "electronics", 60, 11000),
    ("luthier.component.electronics.boutique", "Boutique Electronics", "electronics", 80, 16000),
    ("luthier.component.hardware.standard", "Standard Bridge & Tuners", "hardware", 1, 3500),
    ("luthier.component.hardware.tremolo", "Tremolo Bridge", "hardware", 30, 6500),
    ("luthier.component.hardware.locking_tuners", "Locking Tuners", "hardware", 50, 7000),
    ("luthier.component.hardware.touring", "Touring Hardware", "hardware", 60, 9000),
    ("luthier.component.hardware.brass", "Brass Hardware", "hardware", 70, 11000),
    ("luthier.component.hardware.lightweight_premium", "Premium Lightweight Hardware", "hardware", 90, 17000),
)

SHAPES = (
    ("luthier.shape.guitar.double_cut", "Double Cut", "guitar", 1),
    ("luthier.shape.bass.p_style", "P-Style Bass", "bass", 1),
    ("luthier.shape.guitar.s_style", "S-Style", "guitar", 10),
    ("luthier.shape.guitar.t_style", "T-Style", "guitar", 20),
    ("luthier.shape.bass.j_style", "J-Style Bass", "bass", 30),
    ("luthier.shape.guitar.single_cut", "Single Cut", "guitar", 40),
)


class LuthieryCatalogueService:
    def __init__(self, db_path: str | None = None):
        self.db_path = str(db_path or DB_PATH)

    def ensure_schema(self) -> None:
        sql_path = Path(__file__).resolve().parents[1] / "migrations/sql/171_luthiery_phase2_catalogue.sql"
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(sql_path.read_text())
            self._seed(conn)

    def _seed(self, conn: sqlite3.Connection) -> None:
        for key, name, kind, rarity, cost, quality, affinities, level in MATERIALS:
            conn.execute(
                """INSERT OR IGNORE INTO crafting_materials
                   (key,name,material_type,rarity,cost_cents,quality,stat_affinities_json,required_level)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (key, name, kind, rarity, cost, quality, json.dumps(affinities), level),
            )
        for key, name, part, level, cost in COMPONENTS:
            conn.execute(
                """INSERT OR IGNORE INTO crafting_component_designs
                   (key,name,part_type,cost_cents,required_level)
                   VALUES (?,?,?,?,?)""",
                (key, name, part, cost, level),
            )
        for key, name, instrument_type, level, _asset_key in VISUAL_SHAPES:
            conn.execute(
                """INSERT OR IGNORE INTO instrument_shapes
                   (key,name,instrument_type,required_level) VALUES (?,?,?,?)""",
                (key, name, instrument_type, level),
            )
        for content_type, rows in UNLOCKS.items():
            for level, key, _name in rows:
                conn.execute(
                    """INSERT OR IGNORE INTO crafting_unlocks
                       (content_key,content_type,required_skill,required_level)
                       VALUES (?,?,?,?)""",
                    (key, content_type.rstrip("s"), "luthiery", level),
                )
        conn.execute(
            """INSERT OR IGNORE INTO luthier_supplier_stock(material_id, quantity)
               SELECT id, 100 FROM crafting_materials WHERE enabled = 1"""
        )

    def catalogue(self, luthiery_level: int) -> dict:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            def rows(table: str):
                return [
                    {**dict(row), "locked": int(row["required_level"]) > luthiery_level}
                    for row in conn.execute(
                        f"SELECT * FROM {table} WHERE enabled=1 ORDER BY required_level, id"
                    )
                ]
            return {
                "parts": ["body", "neck", "fretboard", "electronics", "hardware"],
                "materials": rows("crafting_materials"),
                "components": rows("crafting_component_designs"),
                "shapes": [{**row, "visual": visual_definition(row["key"])} for row in rows("instrument_shapes")],
                "skill_levels": {"instrument_finishing": luthiery_level},
            }

    def inventory(self, character_id: int) -> list[dict]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in conn.execute(
                    """SELECT m.key,m.name,i.quantity
                       FROM character_crafting_materials i
                       JOIN crafting_materials m ON m.id=i.material_id
                       WHERE i.character_id=? AND i.quantity>0 ORDER BY m.name""",
                    (character_id,),
                )
            ]

    def purchase(self, character_id: int, material_key: str, quantity: int, luthiery_level: int) -> dict:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            material = conn.execute(
                """SELECT m.*,s.quantity AS stock FROM crafting_materials m
                   JOIN luthier_supplier_stock s ON s.material_id=m.id
                   WHERE m.key=? AND m.enabled=1""",
                (material_key,),
            ).fetchone()
            if not material:
                raise ValueError("Material not available")
            if luthiery_level < material["required_level"]:
                raise ValueError("Material is locked at your current Luthiery level")
            if material["stock"] < quantity:
                raise ValueError("Insufficient supplier stock")
            total = int(material["cost_cents"]) * quantity
            account = conn.execute(
                "SELECT id,balance_cents FROM accounts WHERE user_id=?",
                (character_id,),
            ).fetchone()
            if not account or account["balance_cents"] < total:
                raise ValueError("Insufficient funds")
            new_balance = account["balance_cents"] - total
            conn.execute("UPDATE accounts SET balance_cents=? WHERE id=?", (new_balance, account["id"]))
            cur = conn.execute(
                """INSERT INTO transactions(type,amount_cents,currency,src_account_id)
                   VALUES ('luthiery_material',?,'USD',?)""",
                (total, account["id"]),
            )
            conn.execute(
                """INSERT INTO ledger_entries(account_id,transaction_id,delta_cents,balance_after)
                   VALUES (?,?,?,?)""",
                (account["id"], cur.lastrowid, -total, new_balance),
            )
            conn.execute(
                "UPDATE luthier_supplier_stock SET quantity=quantity-? WHERE material_id=?",
                (quantity, material["id"]),
            )
            conn.execute(
                """INSERT INTO character_crafting_materials(character_id,material_id,quantity)
                   VALUES (?,?,?) ON CONFLICT(character_id,material_id)
                   DO UPDATE SET quantity=quantity+excluded.quantity""",
                (character_id, material["id"], quantity),
            )
            conn.execute(
                """INSERT INTO material_purchase_history
                   (character_id,material_id,quantity,unit_cost_cents,total_cost_cents)
                   VALUES (?,?,?,?,?)""",
                (character_id, material["id"], quantity, material["cost_cents"], total),
            )
            return {"material_key": material_key, "quantity": quantity, "total_cents": total, "balance_cents": new_balance}


    def admin_catalogue(self) -> dict:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return {
                "materials": [dict(row) for row in conn.execute("SELECT * FROM crafting_materials ORDER BY required_level,id")],
                "components": [dict(row) for row in conn.execute("SELECT * FROM crafting_component_designs ORDER BY required_level,id")],
                "shapes": [dict(row) for row in conn.execute("SELECT * FROM instrument_shapes ORDER BY required_level,id")],
            }

    def set_enabled(self, content_type: str, content_key: str, enabled: bool) -> None:
        tables = {
            "material": "crafting_materials",
            "component": "crafting_component_designs",
            "shape": "instrument_shapes",
        }
        table = tables.get(content_type)
        if not table:
            raise ValueError("Unsupported catalogue type")
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                f"UPDATE {table} SET enabled=? WHERE key=?",
                (1 if enabled else 0, content_key),
            )
            if cur.rowcount != 1:
                raise ValueError("Catalogue entry not found")
            conn.execute(
                "UPDATE crafting_unlocks SET enabled=? WHERE content_key=?",
                (1 if enabled else 0, content_key),
            )


luthiery_catalogue_service = LuthieryCatalogueService()
