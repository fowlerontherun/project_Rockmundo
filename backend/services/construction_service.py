"""Service for managing building construction queues and upgrades."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from models.construction import Blueprint, ConstructionTask, LandParcel
from .economy_service import EconomyService, EconomyError
from .property_service import PropertyService
from .venue_service import VenueService


class ConstructionService:
    def __init__(
        self,
        economy: Optional[EconomyService] = None,
        properties: Optional[PropertyService] = None,
        venues: Optional[VenueService] = None,
    ) -> None:
        self.economy = economy or EconomyService()
        self.property_service = properties or PropertyService(economy=self.economy)
        self.venue_service = venues or VenueService(economy=self.economy)
        # ensure dependent schemas
        try:
            self.property_service.ensure_schema()
        except Exception:
            logging.exception("Failed to ensure property schema")
            raise
        try:
            self.venue_service.ensure_schema()
        except Exception:
            logging.exception("Failed to ensure venue schema")
            raise
        self.parcels: Dict[int, LandParcel] = {}
        self.queue: List[ConstructionTask] = []
        self._next_parcel_id = 1

    # ---------------- land management ----------------
    def purchase_land(self, owner_id: int, location: str, size: int, price: int) -> int:
        """Purchase a new land parcel."""
        try:
            self.economy.withdraw(owner_id, price)
        except EconomyError as e:
            raise ValueError(str(e)) from e
        parcel_id = self._next_parcel_id
        self._next_parcel_id += 1
        self.parcels[parcel_id] = LandParcel(parcel_id, owner_id, location, size)
        return parcel_id

    # ---------------- building ----------------
    def submit_design(
        self,
        parcel_id: int,
        blueprint: Blueprint,
        owner_id: int,
        target_id: int,
    ) -> ConstructionTask:
        """Add a blueprint to the build queue for a parcel."""
        if parcel_id not in self.parcels:
            raise ValueError("Parcel not found")
        try:
            self.economy.withdraw(owner_id, blueprint.cost)
        except EconomyError as e:
            raise ValueError(str(e)) from e
        task = ConstructionTask(parcel_id, blueprint, owner_id, target_id, prepaid_cost=blueprint.cost)
        self.queue.append(task)
        return task

    def advance_time(self, units: int = 1) -> List[ConstructionTask]:
        """Advance construction by ``units`` time steps."""
        completed: List[ConstructionTask] = []
        for task in list(self.queue):
            task.remaining -= units
            while task.remaining <= 0:
                task.phase_index += 1
                if task.phase_index >= len(task.blueprint.phases):
                    self._complete_task(task)
                    self.queue.remove(task)
                    completed.append(task)
                    break
                task.remaining += task.blueprint.phases[task.phase_index].duration
        return completed

    def _complete_task(self, task: ConstructionTask) -> None:
        """Apply upgrade effects when a construction task finishes."""
        if task.blueprint.target_type == "property":
            # Re‑deposit prepaid cost so upgrade_property can charge the owner
            self.economy.deposit(task.owner_id, task.prepaid_cost)
            try:
                self.property_service.upgrade_property(task.target_id, task.owner_id)
            except Exception:
                logging.exception("Failed to upgrade property %s", task.target_id)
                return
            effect = task.blueprint.upgrade_effect
            if effect:
                import sqlite3

                with sqlite3.connect(self.property_service.db_path) as conn:
                    cur = conn.cursor()
                    set_clause = ", ".join(f"{k} = {k} + ?" for k in effect)
                    vals = list(effect.values()) + [task.target_id]
                    cur.execute(f"UPDATE properties SET {set_clause} WHERE id = ?", vals)
                    conn.commit()
        elif task.blueprint.target_type == "venue":
            base = self.venue_service.get_venue(task.target_id) or {}
            updates = {k: base.get(k, 0) + v for k, v in task.blueprint.upgrade_effect.items()}
            try:
                self.venue_service.update_venue(task.target_id, updates)
            except Exception:
                logging.exception("Failed to update venue %s", task.target_id)

    # ---------------- helpers ----------------
    def get_queue(self) -> List[Dict[str, int]]:
        """Return a serialisable view of the build queue."""
        return [
            {
                "parcel_id": t.parcel_id,
                "blueprint": t.blueprint.name,
                "phase_index": t.phase_index,
                "remaining": t.remaining,
            }
            for t in self.queue
        ]
