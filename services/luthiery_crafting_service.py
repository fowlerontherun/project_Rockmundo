"""Server-authoritative persistent Luthiery crafting engine (Phase 4)."""
from __future__ import annotations

import hashlib
import json
import random
import re
import sqlite3
from pathlib import Path

from services.luthiery_catalogue_service import LuthieryCatalogueService, DB_PATH
from services.luthiery_stats_service import build_profile\nfrom services.luthiery_balance_service import balance_service

PARTS = ("body", "neck", "fretboard", "electronics", "hardware")
MATERIAL_TYPES_BY_PART = {
    "body": {"body_wood","wood","decorative_wood"},
    "neck": {"wood"},
    "fretboard": {"fretboard_wood","wood"},
    # Electronics/hardware currently use the selected material as a build/finish
    # substrate; until dedicated metal/electronic materials are seeded, general
    # woods remain accepted for these two legacy slots.
    "electronics": {"wood","body_wood","decorative_wood"},
    "hardware": {"wood","body_wood","decorative_wood"},
}
HEX_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")
TIERS = ((30,"Poor"),(45,"Basic"),(60,"Good"),(72,"Excellent"),(84,"Professional"),(94,"Masterwork"),(101,"Legendary"))


class LuthieryCraftingService:
    def __init__(self, db_path: str | None = None):
        self.db_path = str(db_path or DB_PATH)
        self.catalogue = LuthieryCatalogueService(self.db_path)

    def ensure_schema(self):
        self.catalogue.ensure_schema()
        sql = Path(__file__).resolve().parents[1] / "migrations/sql/172_luthiery_phase4_crafting.sql"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript(sql.read_text())

    @staticmethod
    def _tier(score: float) -> str:
        return next(name for ceiling, name in TIERS if score < ceiling)

    @staticmethod
    def _variance(character_id: int, token: str) -> float:
        seed = int(hashlib.sha256(f"{character_id}:{token}".encode()).hexdigest()[:16], 16)
        return random.Random(seed).uniform(-5.0, 5.0)

    @staticmethod
    def _outcome(score: float, character_id: int, token: str) -> tuple[list[str], dict, str | None]:
        seed = int(hashlib.sha256(f"outcome:{character_id}:{token}".encode()).hexdigest()[:16], 16)
        rng = random.Random(seed)
        traits, modifiers, defect = [], {}, None
        if score >= 80:
            traits.append("precision_build")
            modifiers["reliability"] = 2
        if score >= 92:
            traits.append("master_craftsmanship")
            modifiers["playability"] = 3
        # Imperfections are non-destructive and deterministic: the instrument is still produced.
        defect_chance = max(0.0, (45.0 - score) / 100.0)
        if rng.random() < defect_chance:
            defect = rng.choice(("cosmetic_finish_flaw", "minor_setup_issue", "noisy_electronics"))
            traits.append(defect)
            modifiers["reliability"] = modifiers.get("reliability", 0) - 1
        return traits, modifiers, defect

    @staticmethod
    def _validate_advanced_features(shape, resolved, finish_key):
        if finish_key=="luthier.finish.metallic" and not balance_service.feature_enabled("metallic_finishes"):
            raise ValueError("Metallic finishes are currently disabled")
        if int(shape["required_level"])>=80 and not balance_service.feature_enabled("legendary_shapes"):
            raise ValueError("Legendary shapes are currently disabled")
        for _part,material,component in resolved:
            if int(material["required_level"])>=80 and not balance_service.feature_enabled("premium_materials"):
                raise ValueError("Premium materials are currently disabled")
            if component and component["key"]=="luthier.component.electronics.boutique" and not balance_service.feature_enabled("boutique_electronics"):
                raise ValueError("Boutique electronics are currently disabled")

    def admin_preview(self,instrument_type:str,shape_key:str,selections:dict,skills:dict,finish_key:str="luthier.finish.solid",workshop_score:float=50.0,seed_token:str="admin-demo")->dict:
        """Run crafting balance/compatibility calculations without inventory/economy writes."""
        self.ensure_schema()
        if instrument_type not in ("guitar","bass"):raise ValueError("Unsupported instrument type")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory=sqlite3.Row
            shape=conn.execute("SELECT * FROM instrument_shapes WHERE key=? AND enabled=1",(shape_key,)).fetchone()
            level=int(skills.get("luthiery",0))
            if not shape or shape["instrument_type"]!=instrument_type:raise ValueError("Shape is not compatible with this instrument")
            if level<int(shape["required_level"]):raise ValueError("Shape is locked at this demo skill level")
            resolved=[];material_scores=[]
            for part in PARTS:
                choice=selections.get(part) or {};mk=choice.get("material_key");ck=choice.get("component_key")
                material=conn.execute("SELECT * FROM crafting_materials WHERE key=? AND enabled=1",(mk,)).fetchone()
                if not material or level<int(material["required_level"]):raise ValueError(f"{part} material is unavailable or locked")
                component=conn.execute("SELECT * FROM crafting_component_designs WHERE key=? AND part_type=? AND enabled=1",(ck,part)).fetchone() if ck else None
                if ck and (not component or level<int(component["required_level"])):raise ValueError(f"{part} component is unavailable or locked")
                resolved.append((part,material,component))
                mq=max(0.0,min(100.0,55.0+(float(material["quality"])-0.90)*93.75));cb=max(0.0,min(15.0,(float(component["quality"])-0.90)*46.875+5.0)) if component else 0.0
                material_scores.append(min(100.0,mq+cb))
            self._validate_advanced_features(shape,resolved,finish_key)
            specialist=sum(float(skills.get(k,0)) for k in ("woodworking","fretwork","instrument_electronics","instrument_finishing"))/4.0
            material_score=sum(material_scores)/len(material_scores);w=balance_service.quality_weights()
            raw=level*w["skill"]+material_score*w["materials"]+specialist*w["specialist"]+max(0,min(100,workshop_score))*w["workshop"]
            raw+=self._variance(0,seed_token)*(w["variance"]/.05 if w["variance"] else 0)
            score=round(max(max(1.0,level*.35),min(min(100.0,48.0+level*.52),raw)),2);tier=self._tier(score)
            traits,mods,defect=self._outcome(score,0,seed_token);profile=build_profile(resolved,score,skills)
            traits.extend(x["key"] for x in profile["traits"] if x["key"] not in traits);mods.update(profile["gameplay_modifiers"])
            return {"dry_run":True,"quality_score":score,"quality_tier":tier,"traits":traits,"defect":defect,"characteristics":profile["characteristics"],"gameplay_modifiers":mods,"genre_affinities":profile["genre_affinities"],"material_score":round(material_score,2),"specialist_score":round(specialist,2),"workshop_score":workshop_score}

    def craft(self, character_id: int, request_token: str, name: str, instrument_type: str,
              shape_key: str, selections: dict, skills: dict, finish_key: str = "luthier.finish.solid",
              primary_colour: str = "#202020", accent_colour: str | None = None,
              hardware_colour: str = "#c0c0c0", surface_sheen: str = "gloss",
              workshop_score: float = 50.0) -> dict:
        if not request_token.strip():
            raise ValueError("A request token is required")
        if instrument_type not in ("guitar", "bass"):
            raise ValueError("Unsupported instrument type")
        finish_levels={"luthier.finish.solid":1,"luthier.finish.natural":1,"luthier.finish.transparent":20,"luthier.finish.metallic":40}
        if finish_key not in finish_levels:
            raise ValueError("Unsupported instrument finish")
        if surface_sheen not in ("matte","satin","gloss"):
            raise ValueError("Unsupported surface sheen")
        for label, colour, optional in (("primary",primary_colour,False),("accent",accent_colour,True),("hardware",hardware_colour,False)):
            if optional and colour is None: continue
            if not isinstance(colour,str) or not HEX_COLOUR.fullmatch(colour):
                raise ValueError(f"Invalid {label} colour")
        if set(selections) != set(PARTS):
            raise ValueError("Exactly body, neck, fretboard, electronics and hardware are required")
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT crafted_item_id FROM crafting_jobs WHERE character_id=? AND request_token=?",
                (character_id, request_token),
            ).fetchone()
            if existing:
                item = conn.execute("SELECT * FROM crafted_items WHERE id=?", (existing[0],)).fetchone()
                if item:
                    return dict(item)
                raise ValueError("Craft request is already in progress")

            shape = conn.execute(
                "SELECT * FROM instrument_shapes WHERE key=? AND enabled=1", (shape_key,)
            ).fetchone()
            level = int(skills.get("luthiery", 0))
            if int(skills.get("instrument_finishing",0)) < finish_levels[finish_key]:
                raise ValueError(f"Instrument Finishing level {finish_levels[finish_key]} is required for this finish")
            if not shape or shape["instrument_type"] != instrument_type:
                raise ValueError("Shape is not compatible with this instrument")
            if level < int(shape["required_level"]):
                raise ValueError("Shape is locked at your current Luthiery level")

            resolved = []
            material_scores = []
            for part in PARTS:
                choice = selections[part]
                material_key = choice.get("material_key")
                component_key = choice.get("component_key")
                if not material_key:
                    raise ValueError(f"{part} requires a material")
                material = conn.execute(
                    "SELECT * FROM crafting_materials WHERE key=? AND enabled=1", (material_key,)
                ).fetchone()
                if not material or level < int(material["required_level"]):
                    raise ValueError(f"{part} material is unavailable or locked")
                try:
                    material_instruments=json.loads(material["instrument_compatibility_json"] or "[]")
                except (json.JSONDecodeError,TypeError,ValueError):
                    material_instruments=[]
                if instrument_type not in material_instruments:
                    raise ValueError(f"{part} material is incompatible with this instrument")
                if material["material_type"] not in MATERIAL_TYPES_BY_PART[part]:
                    raise ValueError(f"{material['name']} cannot be used for {part}")
                stock = conn.execute(
                    """SELECT quantity FROM character_crafting_materials
                       WHERE character_id=? AND material_id=?""",
                    (character_id, material["id"]),
                ).fetchone()
                if not stock or int(stock[0]) < 1:
                    raise ValueError(f"You do not own the required material for {part}")
                component = None
                if component_key:
                    component = conn.execute(
                        "SELECT * FROM crafting_component_designs WHERE key=? AND part_type=? AND enabled=1",
                        (component_key, part),
                    ).fetchone()
                    if not component or level < int(component["required_level"]):
                        raise ValueError(f"{part} component is unavailable or locked")
                    try:
                        component_instruments=json.loads(component["instrument_compatibility_json"] or "[]")
                    except (json.JSONDecodeError,TypeError,ValueError):
                        component_instruments=[]
                    if instrument_type not in component_instruments:
                        raise ValueError(f"{part} component is incompatible with this instrument")
                resolved.append((part, material, component))
                # Catalogue quality is a multiplier centred around 1.0. Normalise it to
                # a 0-100 crafting contribution: starter woods ~=55, premium woods ~=85.
                material_quality=max(0.0,min(100.0,55.0+(float(material["quality"])-0.90)*93.75))
                component_bonus=max(0.0,min(15.0,(float(component["quality"])-0.90)*46.875+5.0)) if component else 0.0
                material_scores.append(min(100.0,material_quality+component_bonus))

            self._validate_advanced_features(shape,resolved,finish_key)
            specialist = sum(float(skills.get(k, 0)) for k in ("woodworking","fretwork","instrument_electronics","instrument_finishing")) / 4.0
            material_score = min(100.0, sum(material_scores) / len(material_scores))
            # Premium inputs help, but the skill term and skill-dependent ceiling stop novices buying mastery.
            raw = level * .35 + material_score * .35 + specialist * .15 + max(0,min(100,workshop_score)) * .10
            raw += self._variance(character_id, request_token)
            floor = max(1.0, level * .35)
            ceiling = min(100.0, 48.0 + level * .52)
            score = round(max(floor, min(ceiling, raw)), 2)
            tier = self._tier(score)
            traits, modifiers, defect = self._outcome(score, character_id, request_token)
            profile = build_profile(resolved, score, skills)
            traits.extend(t["key"] for t in profile["traits"] if t["key"] not in traits)
            modifiers.update(profile["gameplay_modifiers"])
            modifiers["characteristics"] = profile["characteristics"]
            modifiers["genre_affinities"] = profile["genre_affinities"]
            serial = "RM-" + hashlib.sha256(f"{character_id}:{request_token}:{shape_key}".encode()).hexdigest()[:12].upper()

            job = conn.execute(
                "INSERT INTO crafting_jobs(character_id,request_token,status) VALUES (?,?,'pending')",
                (character_id, request_token),
            )
            cur = conn.execute(
                """INSERT INTO crafted_items
                   (serial_number,creator_character_id,owner_character_id,instrument_type,shape_key,name,
                    primary_colour,accent_colour,finish_key,quality_score,quality_tier,skill_snapshot_json,
                    workshop_snapshot_json,traits_json,stat_modifiers_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (serial, character_id, character_id, instrument_type, shape_key, name.strip()[:80] or "Unnamed Instrument",
                 primary_colour, accent_colour, finish_key, score, tier, json.dumps(skills, sort_keys=True),
                 json.dumps({"score": workshop_score, "hardware_colour": hardware_colour, "surface_sheen": surface_sheen}), json.dumps(traits), json.dumps(modifiers)),
            )
            item_id = cur.lastrowid
            for part, material, component in resolved:
                conn.execute(
                    """INSERT INTO crafted_item_parts(crafted_item_id,part_type,material_key,component_key,quality_contribution)
                       VALUES (?,?,?,?,?)""",
                    (item_id, part, material["key"], component["key"] if component else None, float(material["quality"])),
                )
                changed = conn.execute(
                    """UPDATE character_crafting_materials SET quantity=quantity-1
                       WHERE character_id=? AND material_id=? AND quantity>0""",
                    (character_id, material["id"]),
                )
                if changed.rowcount != 1:
                    raise ValueError("Material inventory changed during crafting")
            conn.execute(
                """INSERT INTO crafted_item_events(crafted_item_id,character_id,event_type,details_json)
                   VALUES (?,?,?,?)""",
                (item_id, character_id, "crafted", json.dumps({"quality": score, "tier": tier, "defect": defect})),
            )
            conn.execute(
                "UPDATE crafting_jobs SET status='completed',crafted_item_id=?,completed_at=datetime('now') WHERE id=?",
                (item_id, job.lastrowid),
            )
            return dict(conn.execute("SELECT * FROM crafted_items WHERE id=?", (item_id,)).fetchone())

    def rework(self, character_id: int, item_id: int, skills: dict) -> dict:
        """One-way improvement action; never rerolls the original craft."""
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            item = conn.execute(
                "SELECT * FROM crafted_items WHERE id=? AND owner_character_id=?", (item_id, character_id)
            ).fetchone()
            if not item:
                raise ValueError("Crafted instrument not found")
            if int(item["rework_count"]) >= 1:
                raise ValueError("This instrument has already been reworked")
            level = int(skills.get("luthiery", 0))
            if level < 20:
                raise ValueError("Luthiery level 20 is required to rework instruments")
            traits = json.loads(item["traits_json"])
            defects = {"cosmetic_finish_flaw", "minor_setup_issue", "noisy_electronics"}
            removed = next((t for t in traits if t in defects), None)
            if not removed:
                raise ValueError("This instrument has no repairable crafting imperfection")
            traits.remove(removed)
            modifiers = json.loads(item["stat_modifiers_json"])
            modifiers["reliability"] = modifiers.get("reliability", 0) + 1
            new_score = min(100.0, float(item["quality_score"]) + 2.0)
            conn.execute(
                """UPDATE crafted_items SET traits_json=?,stat_modifiers_json=?,quality_score=?,
                   quality_tier=?,rework_count=rework_count+1 WHERE id=?""",
                (json.dumps(traits), json.dumps(modifiers), new_score, self._tier(new_score), item_id),
            )
            conn.execute(
                """INSERT INTO crafted_item_events(crafted_item_id,character_id,event_type,details_json)
                   VALUES (?,?, 'reworked', ?)""",
                (item_id, character_id, json.dumps({"removed": removed, "quality_gain": 2.0})),
            )
            return dict(conn.execute("SELECT * FROM crafted_items WHERE id=?", (item_id,)).fetchone())

    def detail(self, character_id: int, item_id: int) -> dict:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            item = conn.execute("SELECT * FROM crafted_items WHERE id=? AND owner_character_id=?", (item_id, character_id)).fetchone()
            if not item:
                raise ValueError("Crafted instrument not found")
            result = dict(item)
            try:
                workshop = json.loads(result.get("workshop_snapshot_json") or "{}")
            except (json.JSONDecodeError, TypeError, ValueError):
                workshop = {}
            result["appearance"] = {
                "instrument_type": result["instrument_type"],
                "shape_key": result["shape_key"],
                "primary_colour": result["primary_colour"],
                "accent_colour": result["accent_colour"],
                "finish_key": result["finish_key"],
                "hardware_colour": workshop.get("hardware_colour", "#c0c0c0"),
                "surface_sheen": workshop.get("surface_sheen", "gloss"),
            }
            result["parts"] = [dict(r) for r in conn.execute(
                """SELECT p.part_type,p.material_key,m.name material_name,p.component_key,c.name component_name,p.quality_contribution
                   FROM crafted_item_parts p
                   LEFT JOIN crafting_materials m ON m.key=p.material_key
                   LEFT JOIN crafting_component_designs c ON c.key=p.component_key
                   WHERE p.crafted_item_id=? ORDER BY CASE p.part_type
                   WHEN 'body' THEN 1 WHEN 'neck' THEN 2 WHEN 'fretboard' THEN 3 WHEN 'electronics' THEN 4 ELSE 5 END""",
                (item_id,),
            )]
            try:
                result["events"] = [dict(r) for r in conn.execute(
                    "SELECT event_type,details_json,created_at FROM crafted_item_events WHERE crafted_item_id=? ORDER BY id DESC", (item_id,)
                )]
            except sqlite3.OperationalError:
                result["events"] = []
            return result

    def set_locked(self, character_id: int, item_id: int, locked: bool) -> dict:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("UPDATE crafted_items SET locked=? WHERE id=? AND owner_character_id=?", (1 if locked else 0, item_id, character_id))
            if cur.rowcount != 1:
                raise ValueError("Crafted instrument not found")
            return dict(conn.execute("SELECT * FROM crafted_items WHERE id=?", (item_id,)).fetchone())

    def inventory(self, character_id: int) -> list[dict]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(
                "SELECT * FROM crafted_items WHERE owner_character_id=? ORDER BY id DESC", (character_id,)
            )]


luthiery_crafting_service = LuthieryCraftingService()
