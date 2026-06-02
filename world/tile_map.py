"""
tile_map.py — Tile types, procedural map generation, district classification.
"""

from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from typing import List, Tuple
import math
import random

import config


class TileType(IntEnum):
    GRASS = 0
    GRASS_LUSH = 1
    ROAD = 2
    SIDEWALK = 3
    WATER = 4
    PLAZA = 5
    DIRT = 6


class District(IntEnum):
    SLUMS = 0
    INDUSTRIAL = 1
    RESIDENTIAL = 2
    DOWNTOWN = 3
    PARK = 4


WALKABLE = {TileType.GRASS, TileType.GRASS_LUSH, TileType.ROAD,
            TileType.SIDEWALK, TileType.PLAZA, TileType.DIRT}


@dataclass
class Tile:
    type: TileType
    district: District
    walkable: bool
    building_id: int = -1     # -1 = no building
    danger: float = 0.0       # 0..1, rises with crime
    light: float = 0.0        # window/streetlight contribution

    def is_walkable(self) -> bool:
        return self.walkable and self.building_id == -1


class TileMap:
    """Grid of tiles. Generated procedurally with a radial district layout."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = []
        self._generate()

    def _generate(self) -> None:
        cx, cy = self.width / 2, self.height / 2
        max_dist = math.hypot(cx, cy)

        self.tiles = [[None] * self.height for _ in range(self.width)]  # type: ignore

        for x in range(self.width):
            for y in range(self.height):
                d_norm = math.hypot(x - cx, y - cy) / max_dist
                district = self._district_for_radius(d_norm)
                ttype, walk = self._base_tile_for_district(district, x, y)
                self.tiles[x][y] = Tile(type=ttype, district=district, walkable=walk)

        self._carve_roads(cx, cy)
        self._carve_river()
        self._sprinkle_parks()

    @staticmethod
    def _district_for_radius(r: float) -> District:
        if r <= 0.18:
            return District.DOWNTOWN
        if r <= 0.45:
            return District.RESIDENTIAL
        if r <= 0.70:
            return District.INDUSTRIAL
        return District.SLUMS

    @staticmethod
    def _base_tile_for_district(d: District, x: int, y: int) -> Tuple[TileType, bool]:
        # Subtle terrain variety
        n = (x * 73 + y * 131) % 17
        if d == District.DOWNTOWN:
            return TileType.PLAZA, True
        if d == District.RESIDENTIAL:
            return (TileType.GRASS_LUSH, True) if n < 4 else (TileType.GRASS, True)
        if d == District.INDUSTRIAL:
            return TileType.DIRT, True
        # slums
        return (TileType.DIRT, True) if n < 5 else (TileType.GRASS, True)

    def _carve_roads(self, cx: float, cy: float) -> None:
        """Carve radial + ring roads."""
        # ring roads at radii 0.25, 0.55, 0.85
        for r_norm in (0.25, 0.55, 0.85):
            r = r_norm * min(self.width, self.height) / 2
            steps = int(r * 8)
            for i in range(steps):
                a = (i / steps) * math.tau
                x = int(cx + math.cos(a) * r)
                y = int(cy + math.sin(a) * r)
                self._set_road(x, y)
                self._set_road(x + 1, y)
                self._set_road(x, y + 1)

        # radial roads
        for angle_deg in range(0, 360, 30):
            a = math.radians(angle_deg)
            for step in range(0, int(min(self.width, self.height) / 2)):
                x = int(cx + math.cos(a) * step)
                y = int(cy + math.sin(a) * step)
                self._set_road(x, y)

    def _set_road(self, x: int, y: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            t = self.tiles[x][y]
            t.type = TileType.ROAD
            t.walkable = True

    def _carve_river(self) -> None:
        """A meandering river along one edge."""
        rng = random.Random(7)
        y = int(self.height * 0.15)
        for x in range(self.width):
            y += rng.choice((-1, -1, 0, 0, 0, 1, 1))
            y = max(2, min(self.height - 3, y))
            for dy in (-1, 0, 1):
                if 0 <= y + dy < self.height:
                    t = self.tiles[x][y + dy]
                    t.type = TileType.WATER
                    t.walkable = False

    def _sprinkle_parks(self) -> None:
        rng = random.Random(13)
        for _ in range(8):
            px = rng.randint(8, self.width - 8)
            py = rng.randint(8, self.height - 8)
            for x in range(px - 3, px + 4):
                for y in range(py - 3, py + 4):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        t = self.tiles[x][y]
                        if t.type not in (TileType.ROAD, TileType.WATER):
                            t.type = TileType.GRASS_LUSH
                            t.district = District.PARK
                            t.walkable = True

    # ── Queries ───────────────────────────────────────────────────────────────
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> Tile:
        return self.tiles[x][y]

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return self.tiles[x][y].is_walkable()

    def find_empty_buildable_tile(self, district: District, rng: random.Random) -> Tuple[int, int]:
        """Find a tile in the given district with no building and walkable terrain."""
        for _ in range(2000):
            x = rng.randint(1, self.width - 2)
            y = rng.randint(1, self.height - 2)
            t = self.tiles[x][y]
            if (t.district == district and t.building_id == -1
                    and t.type in (TileType.GRASS, TileType.GRASS_LUSH, TileType.DIRT)):
                return x, y
        # Fallback: any free tile
        for _ in range(2000):
            x = rng.randint(1, self.width - 2)
            y = rng.randint(1, self.height - 2)
            t = self.tiles[x][y]
            if t.building_id == -1 and t.type in (TileType.GRASS, TileType.GRASS_LUSH, TileType.DIRT):
                return x, y
        raise RuntimeError("No buildable tile found")
