"""
tile_map.py — Tile types and a Manhattan-inspired procedural map.

Layout (top-down, +x = east, +y = south):

┌────────────────────────────────────────────────────────────────┐
│ ~~~~~  SLUMS / TENEMENTS                                      │  (north — Harlem-ish)
│ ~~~~~  ────────────────────────────────────────                │
│ HUDSON                                                         │
│ ~~~~~  RESIDENTIAL  ┌─────────────┐    RESIDENTIAL              │
│ ~~~~~               │  CENTRAL    │                            │
│ ~~~~~               │  PARK       │                            │
│ ~~~~~               └─────────────┘                            │
│ ~~~~~  RESIDENTIAL                       RESIDENTIAL           │
│ ~~~~~  ────────────────────────────────────────                │
│ ~~~~~  INDUSTRIAL / WAREHOUSES                                 │
│ ~~~~~  ────────────────────────────────────────                │
│ ~~~~~  DOWNTOWN (financial district)                           │  (south — Wall St-ish)
└────────────────────────────────────────────────────────────────┘

Roads form a strict grid: avenues run N–S, streets run E–W, with a
wider "Broadway" diagonal cutting across. Sidewalks border every road.
"""

from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass
from typing import List, Tuple
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


# ── Grid geometry ────────────────────────────────────────────────────────────
# Avenues (N–S) and streets (E–W) at fixed spacings. These produce the
# characteristic narrow-block-wide-avenue Manhattan feel.
_AVENUE_SPACING = 10   # tiles between N–S avenues
_STREET_SPACING = 5    # tiles between E–W streets
_AVENUE_WIDTH = 2      # tiles wide
_STREET_WIDTH = 1      # tiles wide
_HUDSON_WIDTH = 5      # westernmost columns are river


class TileMap:
  """Grid of tiles. Manhattan-style: rectangular districts, grid streets,
  a river on the west edge, and a central park rectangle."""

  def __init__(self, width: int, height: int):
      self.width = width
      self.height = height
      self.tiles: List[List[Tile]] = []
      self._generate()

  def _generate(self) -> None:
      # Phase 1: every tile starts as the district's base terrain.
      self.tiles = [[None] * self.height for _ in range(self.width)]  # type: ignore
      for x in range(self.width):
          for y in range(self.height):
              district = self._district_for_xy(x, y)
              ttype, walk = self._base_tile_for_district(district, x, y)
              self.tiles[x][y] = Tile(type=ttype, district=district, walkable=walk)

      # Phase 2: carve features in order — river first (can't be paved over),
      # then park, then the road grid (roads override park boundaries),
      # then sidewalks around roads.
      self._carve_hudson()
      self._carve_central_park()
      self._carve_grid()
      self._carve_sidewalks()
      self._sprinkle_pocket_parks()

  # ── District layout (rectangular bands instead of radial rings) ──────────
  def _district_for_xy(self, x: int, y: int) -> District:
      # Hudson river occupies the westernmost band — treated as SLUMS for
      # district purposes but tiles get overwritten as WATER below.
      if x < _HUDSON_WIDTH:
          return District.SLUMS

      # North–south bands, like Manhattan from Harlem (top) to Wall St (bottom).
      h = self.height
      if y < h * 0.15:
          return District.SLUMS          # Harlem-ish
      if y < h * 0.55:
          return District.RESIDENTIAL    # Upper / Midtown residential
      if y < h * 0.78:
          return District.INDUSTRIAL     # Garment / Meatpacking / warehouses
      return District.DOWNTOWN           # Financial District

  @staticmethod
  def _base_tile_for_district(d: District, x: int, y: int) -> Tuple[TileType, bool]:
      # Sub-tile variety via a cheap hash.
      n = (x * 73 + y * 131) % 17
      if d == District.DOWNTOWN:
          return TileType.PLAZA, True
      if d == District.RESIDENTIAL:
          return (TileType.GRASS_LUSH, True) if n < 4 else (TileType.GRASS, True)
      if d == District.INDUSTRIAL:
          return TileType.DIRT, True
      # slums / harlem
      return (TileType.DIRT, True) if n < 5 else (TileType.GRASS, True)

  # ── Carving features ─────────────────────────────────────────────────────
  def _carve_hudson(self) -> None:
      """Hudson river along the western edge with a slightly irregular bank."""
      rng = random.Random(7)
      for y in range(self.height):
          bank = _HUDSON_WIDTH + rng.choice((-1, 0, 0, 1))
          bank = max(2, min(_HUDSON_WIDTH + 2, bank))
          for x in range(bank):
              t = self.tiles[x][y]
              t.type = TileType.WATER
              t.walkable = False

  def _carve_central_park(self) -> None:
      """Big rectangular park, like Central Park, in the residential band."""
      # Roughly the central third horizontally, upper-middle vertically.
      x0 = int(self.width * 0.38)
      x1 = int(self.width * 0.62)
      y0 = int(self.height * 0.22)
      y1 = int(self.height * 0.48)
      for x in range(x0, x1):
          for y in range(y0, y1):
              if not (0 <= x < self.width and 0 <= y < self.height):
                  continue
              t = self.tiles[x][y]
              if t.type == TileType.WATER:
                  continue
              # Pond near the top
              if (x - (x0 + (x1 - x0) // 2)) ** 2 + (y - (y0 + 3)) ** 2 < 9:
                  t.type = TileType.WATER
                  t.walkable = False
              else:
                  t.type = TileType.GRASS_LUSH
                  t.walkable = True
              t.district = District.PARK

  def _carve_grid(self) -> None:
      """Strict avenue (N–S) + street (E–W) grid east of the Hudson."""
      # Avenues — vertical roads.
      for ax in range(_HUDSON_WIDTH + 3, self.width, _AVENUE_SPACING):
          for dx in range(_AVENUE_WIDTH):
              col = ax + dx
              if 0 <= col < self.width:
                  for y in range(self.height):
                      self._paint_road(col, y)

      # Streets — horizontal roads.
      for sy in range(3, self.height, _STREET_SPACING):
          for dy in range(_STREET_WIDTH):
              row = sy + dy
              if 0 <= row < self.height:
                  for x in range(_HUDSON_WIDTH, self.width):
                      self._paint_road(x, row)

      # Broadway — a diagonal "wide" road cutting NW → SE.
      for step in range(0, max(self.width, self.height)):
          x = _HUDSON_WIDTH + 2 + step
          y = int(step * 0.55)
          for dx in range(-1, 2):
              for dy in range(-1, 2):
                  self._paint_road(x + dx, y + dy)
          if x >= self.width or y >= self.height:
              break

  def _paint_road(self, x: int, y: int) -> None:
      if not self.in_bounds(x, y):
          return
      t = self.tiles[x][y]
      if t.type == TileType.WATER:
          return  # don't pave the Hudson
      t.type = TileType.ROAD
      t.walkable = True

  def _carve_sidewalks(self) -> None:
      """Any non-road tile adjacent to a road becomes a sidewalk."""
      to_set: List[Tuple[int, int]] = []
      for x in range(self.width):
          for y in range(self.height):
              t = self.tiles[x][y]
              if t.type in (TileType.ROAD, TileType.WATER):
                  continue
              # Check 4-neighbours
              for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                  if (0 <= nx < self.width and 0 <= ny < self.height
                          and self.tiles[nx][ny].type == TileType.ROAD):
                      to_set.append((x, y))
                      break
      for (x, y) in to_set:
          t = self.tiles[x][y]
          # Keep park grass / water as-is; sidewalk only on neutral terrain.
          if t.type in (TileType.GRASS_LUSH,) and t.district == District.PARK:
              continue
          t.type = TileType.SIDEWALK
          t.walkable = True

  def _sprinkle_pocket_parks(self) -> None:
      """A handful of small green squares scattered across residential blocks."""
      rng = random.Random(13)
      for _ in range(6):
          px = rng.randint(_HUDSON_WIDTH + 4, self.width - 6)
          py = rng.randint(4, self.height - 6)
          # Avoid clobbering Central Park area
          t0 = self.tiles[px][py]
          if t0.district == District.PARK:
              continue
          for x in range(px - 1, px + 2):
              for y in range(py - 1, py + 2):
                  if 0 <= x < self.width and 0 <= y < self.height:
                      t = self.tiles[x][y]
                      if t.type not in (TileType.ROAD, TileType.WATER, TileType.SIDEWALK):
                          t.type = TileType.GRASS_LUSH
                          t.district = District.PARK
                          t.walkable = True

  # ── Queries ──────────────────────────────────────────────────────────────
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
      # Fallback: any free tile (skip water + roads + sidewalks).
      for _ in range(2000):
          x = rng.randint(1, self.width - 2)
          y = rng.randint(1, self.height - 2)
          t = self.tiles[x][y]
          if t.building_id == -1 and t.type in (TileType.GRASS, TileType.GRASS_LUSH, TileType.DIRT):
              return x, y
      raise RuntimeError("No buildable tile found")
