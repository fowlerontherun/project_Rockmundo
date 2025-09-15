from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.quest import (
    QuestDB,
    QuestStageDB,
    QuestBranchDB,
    QuestReward,
    Quest,
    QuestStage,
)

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class QuestAdminService:
    """CRUD operations for quest definitions stored in SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    initial_stage TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quest_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quest_id INTEGER NOT NULL REFERENCES quests(id),
                    stage_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    reward_type TEXT,
                    reward_amount INTEGER
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quest_branches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage_id INTEGER NOT NULL REFERENCES quest_stages(id),
                    choice TEXT NOT NULL,
                    next_stage_id TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    def _validate_branches(self, stages: List[Dict[str, Any]]) -> None:
        stage_ids = {s["id"] for s in stages}
        for st in stages:
            for dest in st.get("branches", {}).values():
                if dest not in stage_ids:
                    raise ValueError(f"Invalid branch destination: {dest}")

    # ------------------------------------------------------------------
    def _from_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize builder graph payload into quest stages."""
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        stages: List[Dict[str, Any]] = []
        for node in nodes:
            node_id = node.get("id")
            ndata = node.get("data", {})
            branches: Dict[str, str] = {}
            for edge in edges:
                if edge.get("source") == node_id:
                    label = edge.get("label") or edge.get("id") or ""
                    branches[label] = edge.get("target")
            stages.append(
                {
                    "id": node_id,
                    "description": ndata.get("description", ""),
                    "reward": ndata.get("reward"),
                    "branches": branches,
                }
            )
        return {
            "name": data.get("name", "Unnamed"),
            "initial_stage": data.get("initial_stage") or (nodes[0]["id"] if nodes else ""),
            "stages": stages,
        }

    # ------------------------------------------------------------------
    def create_from_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._from_graph(data)
        return self.create_quest(
            name=payload["name"],
            stages=payload["stages"],
            initial_stage=payload["initial_stage"],
        )

    # ------------------------------------------------------------------
    def preview_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._from_graph(data)
        self._validate_branches(payload["stages"])
        return {
            "name": payload["name"],
            "initial_stage": payload["initial_stage"],
            "stages": {s["id"]: s for s in payload["stages"]},
        }

    # ------------------------------------------------------------------
    def validate_graph(self, data: Dict[str, Any]) -> None:
        payload = self._from_graph(data)
        self._validate_branches(payload["stages"])

    # ------------------------------------------------------------------
    def create_quest(self, name: str, stages: List[Dict[str, Any]], initial_stage: str) -> Dict[str, Any]:
        self._validate_branches(stages)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO quests (name, version, initial_stage) VALUES (?, 1, ?)",
                (name, initial_stage),
            )
            quest_id = cur.lastrowid
            stage_row_ids: Dict[str, int] = {}
            for st in stages:
                reward = st.get("reward")
                cur.execute(
                    """
                    INSERT INTO quest_stages (quest_id, stage_id, description, reward_type, reward_amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        quest_id,
                        st["id"],
                        st["description"],
                        reward.get("type") if reward else None,
                        reward.get("amount") if reward else None,
                    ),
                )
                stage_row_ids[st["id"]] = cur.lastrowid
            for st in stages:
                for choice, dest in st.get("branches", {}).items():
                    cur.execute(
                        "INSERT INTO quest_branches (stage_id, choice, next_stage_id) VALUES (?, ?, ?)",
                        (stage_row_ids[st["id"]], choice, dest),
                    )
            conn.commit()
        return self.get_quest(quest_id)

    # ------------------------------------------------------------------
    def get_quest(self, quest_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, version, initial_stage FROM quests WHERE id = ?",
                (quest_id,),
            )
            qrow = cur.fetchone()
            if not qrow:
                return None
            cur.execute(
                "SELECT id, stage_id, description, reward_type, reward_amount FROM quest_stages WHERE quest_id = ?",
                (quest_id,),
            )
            stages = {}
            id_map = {}
            for row in cur.fetchall():
                id_map[row["id"]] = row["stage_id"]
                reward = None
                if row["reward_type"]:
                    reward = {"type": row["reward_type"], "amount": row["reward_amount"]}
                stages[row["stage_id"]] = {
                    "id": row["stage_id"],
                    "description": row["description"],
                    "reward": reward,
                    "branches": {},
                }
            for db_id, code in id_map.items():
                cur.execute(
                    "SELECT choice, next_stage_id FROM quest_branches WHERE stage_id = ?",
                    (db_id,),
                )
                branches = {r["choice"]: r["next_stage_id"] for r in cur.fetchall()}
                stages[code]["branches"] = branches
            return {
                "id": qrow["id"],
                "name": qrow["name"],
                "version": qrow["version"],
                "initial_stage": qrow["initial_stage"],
                "stages": stages,
            }

    # ------------------------------------------------------------------
    def update_stage(
        self,
        quest_id: int,
        stage_id: str,
        description: Optional[str] = None,
        branches: Optional[Dict[str, str]] = None,
        reward: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM quest_stages WHERE quest_id = ? AND stage_id = ?",
                (quest_id, stage_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            stage_db_id = row["id"]
            if description is not None or reward is not None:
                cur.execute(
                    """
                    UPDATE quest_stages
                    SET description = COALESCE(?, description),
                        reward_type = ?,
                        reward_amount = ?
                    WHERE id = ?
                    """,
                    (
                        description,
                        reward.get("type") if reward else None,
                        reward.get("amount") if reward else None,
                        stage_db_id,
                    ),
                )
            if branches is not None:
                # validate branch destinations
                cur.execute(
                    "SELECT stage_id FROM quest_stages WHERE quest_id = ?",
                    (quest_id,),
                )
                valid = {r["stage_id"] for r in cur.fetchall()}
                for dest in branches.values():
                    if dest not in valid:
                        raise ValueError(f"Invalid branch destination: {dest}")
                cur.execute("DELETE FROM quest_branches WHERE stage_id = ?", (stage_db_id,))
                for choice, dest in branches.items():
                    cur.execute(
                        "INSERT INTO quest_branches (stage_id, choice, next_stage_id) VALUES (?, ?, ?)",
                        (stage_db_id, choice, dest),
                    )
            conn.commit()
        quest = self.get_quest(quest_id)
        return quest["stages"].get(stage_id) if quest else None

    # ------------------------------------------------------------------
    def version_quest(self, quest_id: int) -> Optional[Dict[str, Any]]:
        quest = self.get_quest(quest_id)
        if not quest:
            return None
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO quests (name, version, initial_stage) VALUES (?, ?, ?)",
                (quest["name"], quest["version"] + 1, quest["initial_stage"]),
            )
            new_id = cur.lastrowid
            stage_map: Dict[str, int] = {}
            for st in quest["stages"].values():
                reward = st.get("reward")
                cur.execute(
                    """
                    INSERT INTO quest_stages (quest_id, stage_id, description, reward_type, reward_amount)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        new_id,
                        st["id"],
                        st["description"],
                        reward.get("type") if reward else None,
                        reward.get("amount") if reward else None,
                    ),
                )
                stage_map[st["id"]] = cur.lastrowid
            for st in quest["stages"].values():
                for choice, dest in st.get("branches", {}).items():
                    cur.execute(
                        "INSERT INTO quest_branches (stage_id, choice, next_stage_id) VALUES (?, ?, ?)",
                        (stage_map[st["id"]], choice, dest),
                    )
            conn.commit()
        return self.get_quest(new_id)

    # ------------------------------------------------------------------
    def delete_quest(self, quest_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM quest_branches WHERE stage_id IN (SELECT id FROM quest_stages WHERE quest_id = ?)",
                (quest_id,),
            )
            cur.execute("DELETE FROM quest_stages WHERE quest_id = ?", (quest_id,))
            cur.execute("DELETE FROM quests WHERE id = ?", (quest_id,))
            conn.commit()
