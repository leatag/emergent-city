"""
persistence.py — Save and load the entire world to/from a JSON file.
Snapshots include time, tile map (compact), buildings, agents, factions.
"""

from __future__ import annotations
import json
import os
import gzip
from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from world.world import World


def save_world(world: "World", path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = {
        "version": 1,
        "tick": world.tick_count,
        "time": world.time_system.to_dict(),
        "tile_map": world.tile_map.to_compact(),
        "buildings": [b.to_dict() for b in world.buildings.buildings],
        "agents": [a.to_dict() for a in world.agents],
        "factions": world.factions.to_dict(),
        "economy": world.economy.to_dict(),
    }
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if path.endswith(".gz"):
        with gzip.open(path, "wb") as f:
            f.write(raw)
    else:
        with open(path, "wb") as f:
            f.write(raw)


def load_world(world: "World", path: str) -> bool:
    if not os.path.exists(path):
        return False
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as f:
            raw = f.read()
    else:
        with open(path, "rb") as f:
            raw = f.read()
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("version") != 1:
        return False
    world.tick_count = payload["tick"]
    world.time_system.from_dict(payload["time"])
    world.tile_map.from_compact(payload["tile_map"])
    world.buildings.from_dicts(payload["buildings"])
    world.agents.clear()
    from agents.agent import Agent
    for ad in payload["agents"]:
        world.agents.append(Agent.from_dict(ad, world))
    world.factions.from_dict(payload["factions"])
    world.economy.from_dict(payload["economy"])
    return True
