"""
save_load.py — Ctrl+S to save, Ctrl+L to load. Uses world.snapshot() and
world.restore() under the hood; writes JSON to config.SAVE_FILE_PATH.
"""

from __future__ import annotations
import json
import logging
import os
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from world.world import World

log = logging.getLogger(__name__)


class SaveLoad:
    def __init__(self, world: "World") -> None:
        self.world = world
        self.path = getattr(config, "SAVE_FILE_PATH", "emergent_city_save.json")

    def save(self) -> bool:
        try:
            data = self.world.snapshot()
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log.info("Saved world to %s", self.path)
            return True
        except Exception as exc:
            log.exception("Save failed: %s", exc)
            return False

    def load(self) -> bool:
        if not os.path.exists(self.path):
            log.warning("No save file at %s", self.path)
            return False
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.world.restore(data)
            log.info("Loaded world from %s", self.path)
            return True
        except Exception as exc:
            log.exception("Load failed: %s", exc)
            return False
