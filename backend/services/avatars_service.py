# File: backend/services/avatars_service.py
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class AvatarError(Exception):
    pass

ALLOWED_SLOTS = [
    "headwear", "glasses", "mask",
    "top", "bottom", "shoes",
    "instrument_skin", "backdrop", "special"
]

ALLOWED_BODY_TYPES = ["slim", "average", "athletic", "plus"]
ALLOWED_INSTRUMENTS = ["guitar", "bass", "drums", "keys", "vocals"]
ALLOWED_POSES = ["idle", "strum", "guitar-solo", "mic-stand", "drum-fill", "keys-solo"]

@dataclass
class AvatarIn:
    user_id: int
    display_name: Optional[str] = None
    body_type: Optional[str] = None
    face: Optional[str] = None
    hair: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    instrument: Optional[str] = None
    outfit_theme: Optional[str] = None
    pose: Optional[str] = None
    render_seed: Optional[str] = None

class AvatarsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- Schema --------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS avatars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                display_name TEXT,
                body_type TEXT,
                face TEXT,
                hair TEXT,
                hair_color TEXT,
                eye_color TEXT,
                skin_tone TEXT,
                instrument TEXT,
                outfit_theme TEXT,
                pose TEXT,
                render_seed TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS avatar_equipped_skins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                avatar_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                skin_id INTEGER NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(avatar_id, slot)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS avatar_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skin_id INTEGER NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1,
                UNIQUE(user_id, skin_id)
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_avatars_user ON avatars(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_inv_user ON avatar_inventory(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_equipped_avatar ON avatar_equipped_skins(avatar_id)")
            conn.commit()

    # -------- Validation --------
    def _validate_fields(self, data: Dict[str, Any]) -> None:
        bt = data.get("body_type")
        if bt and bt not in ALLOWED_BODY_TYPES:
            raise AvatarError(f"Invalid body_type. Allowed: {ALLOWED_BODY_TYPES}")
        ins = data.get("instrument")
        if ins and ins not in ALLOWED_INSTRUMENTS:
            raise AvatarError(f"Invalid instrument. Allowed: {ALLOWED_INSTRUMENTS}")
        pose = data.get("pose")
        if pose and pose not in ALLOWED_POSES:
            raise AvatarError(f"Invalid pose. Allowed: {ALLOWED_POSES}")
        # Simple compatibility rule examples
        if ins == "drums" and pose == "guitar-solo":
            raise AvatarError("Pose 'guitar-solo' incompatible with instrument 'drums'")

    # -------- Avatars --------
    def create_avatar(self, payload: AvatarIn) -> int:
        data = payload.__dict__.copy()
        self._validate_fields(data)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO avatars (user_id, display_name, body_type, face, hair, hair_color, eye_color, skin_tone,
                                     instrument, outfit_theme, pose, render_seed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["user_id"], data.get("display_name"), data.get("body_type"), data.get("face"),
                data.get("hair"), data.get("hair_color"), data.get("eye_color"), data.get("skin_tone"),
                data.get("instrument"), data.get("outfit_theme"), data.get("pose"), data.get("render_seed")
            ))
            conn.commit()
            return cur.lastrowid

    def get_avatar(self, avatar_id: int) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM avatars WHERE id = ?", (avatar_id,))
            row = cur.fetchone()
            if not row:
                raise AvatarError("Avatar not found")
            avatar = dict(row)
            cur.execute("SELECT slot, skin_id FROM avatar_equipped_skins WHERE avatar_id = ?", (avatar_id,))
            equipped = {r["slot"]: r["skin_id"] for r in cur.fetchall()}
            avatar["equipped"] = equipped
            return avatar

    def list_avatars(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if user_id is None:
                cur.execute("SELECT * FROM avatars ORDER BY created_at DESC")
            else:
                cur.execute("SELECT * FROM avatars WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            return [dict(r) for r in cur.fetchall()]

    def update_avatar(self, avatar_id: int, fields: Dict[str, Any]) -> None:
        """Update an avatar and return the updated record.

        ``fields`` is a dictionary of column names to update.  Only a
        predefined set of columns may be modified and any unknown keys are
        ignored.  When the update succeeds the freshly updated avatar is
        returned.  If ``fields`` is empty the current avatar state is
        returned unchanged.
        """

        if not fields:
            # Nothing to update; simply return the current record for
            # convenience so callers always receive avatar data.
            return self.get_avatar(avatar_id)

        self._validate_fields(fields)
        allowed = [
            "display_name",
            "body_type",
            "face",
            "hair",
            "hair_color",
            "eye_color",
            "skin_tone",
            "instrument",
            "outfit_theme",
            "pose",
            "render_seed",
        ]
        sets, vals = [], []
        for k in allowed:
            if k in fields:
                sets.append(f"{k} = ?")
                vals.append(fields[k])

        if not sets:
            return self.get_avatar(avatar_id)

        vals.append(avatar_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE avatars SET {', '.join(sets)}, updated_at = datetime('now') WHERE id = ?",
                vals,
            )
            if cur.rowcount == 0:
                raise AvatarError("Avatar not found")
            conn.commit()

        return self.get_avatar(avatar_id)

    def delete_avatar(self, avatar_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM avatar_equipped_skins WHERE avatar_id = ?", (avatar_id,))
            cur.execute("DELETE FROM avatars WHERE id = ?", (avatar_id,))
            if cur.rowcount == 0:
                raise AvatarError("Avatar not found")
            conn.commit()

    # -------- Inventory --------
    def grant_skin_to_user(self, user_id: int, skin_id: int, qty: int = 1) -> None:
        if qty <= 0:
            raise AvatarError("qty must be > 0")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO avatar_inventory (user_id, skin_id, qty)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, skin_id) DO UPDATE SET qty = avatar_inventory.qty + excluded.qty
            """, (user_id, skin_id, qty))
            conn.commit()

    def list_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM avatar_inventory WHERE user_id = ? ORDER BY skin_id ASC", (user_id,))
            return [dict(r) for r in cur.fetchall()]

    # -------- Equip / Unequip --------
    def equip_skin(self, avatar_id: int, slot: str, skin_id: int) -> None:
        if slot not in ALLOWED_SLOTS:
            raise AvatarError(f"Invalid slot. Allowed: {ALLOWED_SLOTS}")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # find user of avatar
            cur.execute("SELECT user_id FROM avatars WHERE id = ?", (avatar_id,))
            row = cur.fetchone()
            if not row:
                raise AvatarError("Avatar not found")
            user_id = row["user_id"]
            # check inventory
            cur.execute("SELECT qty FROM avatar_inventory WHERE user_id = ? AND skin_id = ?", (user_id, skin_id))
            inv = cur.fetchone()
            if not inv or int(inv["qty"]) <= 0:
                raise AvatarError("User does not own this skin")
            # upsert equip
            cur.execute("""
                INSERT INTO avatar_equipped_skins (avatar_id, slot, skin_id)
                VALUES (?, ?, ?)
                ON CONFLICT(avatar_id, slot) DO UPDATE SET skin_id = excluded.skin_id
            """, (avatar_id, slot, skin_id))
            conn.commit()

    def unequip_skin(self, avatar_id: int, slot: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM avatar_equipped_skins WHERE avatar_id = ? AND slot = ?", (avatar_id, slot))
            conn.commit()

    def list_equipped(self, avatar_id: int) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT slot, skin_id FROM avatar_equipped_skins WHERE avatar_id = ?", (avatar_id,))
            return {r["slot"]: r["skin_id"] for r in cur.fetchall()}
