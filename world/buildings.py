"""
buildings.py — Building types, placement, and per-building state.
"""

from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random

import config
from world.tile_map import TileMap, District, TileType


class BuildingType(IntEnum):
    HOUSE = 0
    HOUSE_WEALTHY = 1
    SHACK = 2
    SHOP = 3
    FACTORY = 4
    BAR = 5
    PARK_BENCH = 6
    CHURCH = 7
    POLICE_STATION = 8


@dataclass
class Building:
    id: int
    type: BuildingType
    x: int
    y: int
    w: int
    h: int
    district: District
    capacity: int = 4
    residents: List[int] = field(default_factory=list)   # agent ids
    workers: List[int] = field(default_factory=list)
    owner_id: int = -1
    stock_food: float = 0.0
    stock_tool: float = 0.0
    stock_luxury: float = 0.0
    quality: float = 0.5     # 0..1, affects mood for residents
    on_fire: bool = False
    fire_intensity: float = 0.0

    def tiles(self) -> List[Tuple[int, int]]:
        return [(self.x + dx, self.y + dy) for dx in range(self.w) for dy in range(self.h)]

    @property
    def is_residential(self) -> bool:
        return self.type in (BuildingType.HOUSE, BuildingType.HOUSE_WEALTHY, BuildingType.SHACK)

    @property
    def is_workplace(self) -> bool:
        return self.type in (BuildingType.SHOP, BuildingType.FACTORY,
                             BuildingType.BAR, BuildingType.CHURCH,
                             BuildingType.POLICE_STATION)


class BuildingRegistry:
    """All buildings in the world, plus placement helpers."""

    def __init__(self, tile_map: TileMap, rng: random.Random):
        self.tile_map = tile_map
        self.rng = rng
        self.buildings: List[Building] = []
        self._next_id = 0

    def populate(self) -> None:
        """Procedurally place housing, shops, factories, etc."""
        layouts = [
            (BuildingType.HOUSE_WEALTHY, District.DOWNTOWN,    20, 2, 2),
            (BuildingType.SHOP,          District.DOWNTOWN,    14, 2, 2),
            (BuildingType.BAR,           District.DOWNTOWN,     4, 2, 2),
            (BuildingType.CHURCH,        District.DOWNTOWN,     2, 3, 3),
            (BuildingType.POLICE_STATION,District.DOWNTOWN,     2, 2, 2),

            (BuildingType.HOUSE,         District.RESIDENTIAL, 60, 2, 2),
            (BuildingType.SHOP,          District.RESIDENTIAL, 10, 2, 2),
            (BuildingType.BAR,           District.RESIDENTIAL,  5, 2, 2),

            (BuildingType.FACTORY,       District.INDUSTRIAL,  10, 3, 3),
            (BuildingType.HOUSE,         District.INDUSTRIAL,  15, 2, 2),

            (BuildingType.SHACK,         District.SLUMS,       50, 2, 2),
            (BuildingType.SHOP,          District.SLUMS,        5, 2, 2),
            (BuildingType.BAR,           District.SLUMS,        4, 2, 2),
        ]

        for btype, district, count, w, h in layouts:
            placed = 0
            attempts = 0
            while placed < count and attempts < count * 30:
                attempts += 1
                try:
                    x, y = self.tile_map.find_empty_buildable_tile(district, self.rng)
                except RuntimeError:
                    break
                if self._can_place(x, y, w, h):
                    self._place(btype, x, y, w, h, district)
                    placed += 1

    def _can_place(self, x: int, y: int, w: int, h: int) -> bool:
        if not (0 <= x and x + w < self.tile_map.width
                and 0 <= y and y + h < self.tile_map.height):
            return False
        for dx in range(-1, w + 1):
            for dy in range(-1, h + 1):
                tx, ty = x + dx, y + dy
                if not (0 <= tx < self.tile_map.width and 0 <= ty < self.tile_map.height):
                    return False
                t = self.tile_map.get(tx, ty)
                if 0 <= dx < w and 0 <= dy < h:
                    if t.building_id != -1:
                        return False
                    if t.type in (TileType.ROAD, TileType.WATER):
                        return False
        return True

    def _place(self, btype: BuildingType, x: int, y: int, w: int, h: int, district: District) -> Building:
        b = Building(
            id=self._next_id,
            type=btype, x=x, y=y, w=w, h=h, district=district,
            quality=self._quality_for(btype, district),
            capacity=self._capacity_for(btype),
        )
        self._next_id += 1
        for tx, ty in b.tiles():
            t = self.tile_map.get(tx, ty)
            t.building_id = b.id
            t.walkable = False
        self.buildings.append(b)
        return b

    @staticmethod
    def _quality_for(btype: BuildingType, district: District) -> float:
        base = {
            BuildingType.HOUSE_WEALTHY: 0.85,
            BuildingType.HOUSE: 0.55,
            BuildingType.SHACK: 0.20,
            BuildingType.SHOP: 0.5,
            BuildingType.FACTORY: 0.3,
            BuildingType.BAR: 0.6,
            BuildingType.CHURCH: 0.8,
            BuildingType.POLICE_STATION: 0.7,
        }.get(btype, 0.5)
        return max(0.0, min(1.0, base))

    @staticmethod
    def _capacity_for(btype: BuildingType) -> int:
        return {
            BuildingType.HOUSE_WEALTHY: 5,
            BuildingType.HOUSE: 4,
            BuildingType.SHACK: 6,
            BuildingType.SHOP: 3,
            BuildingType.FACTORY: 8,
            BuildingType.BAR: 4,
            BuildingType.CHURCH: 2,
            BuildingType.POLICE_STATION: 4,
        }.get(btype, 4)

    # ── Queries ───────────────────────────────────────────────────────────────
    def residences(self) -> List[Building]:
        return [b for b in self.buildings if b.is_residential]

    def workplaces(self) -> List[Building]:
        return [b for b in self.buildings if b.is_workplace]

    def of_type(self, btype: BuildingType) -> List[Building]:
        return [b for b in self.buildings if b.type == btype]

    def get(self, building_id: int) -> Optional[Building]:
        if 0 <= building_id < len(self.buildings):
            return self.buildings[building_id]
        return None
