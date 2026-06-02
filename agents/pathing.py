"""
pathing.py — A* pathfinder on the tile grid.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
import heapq

from world.tile_map import TileMap


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    # Octile distance
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return (dx + dy) + (1.4142 - 2) * min(dx, dy)


NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1),
             (1, 1), (1, -1), (-1, 1), (-1, -1))


def find_path(tile_map: TileMap,
              start: Tuple[int, int],
              goal: Tuple[int, int],
              max_iter: int = 4000) -> Optional[List[Tuple[int, int]]]:
    if start == goal:
        return [start]
    if not tile_map.in_bounds(*goal):
        return None

    open_set: list = []
    heapq.heappush(open_set, (0.0, start))
    came: dict = {}
    g: dict = {start: 0.0}
    it = 0

    while open_set and it < max_iter:
        it += 1
        _, current = heapq.heappop(open_set)
        if current == goal:
            return _reconstruct(came, current)

        for dx, dy in NEIGHBORS:
            nx, ny = current[0] + dx, current[1] + dy
            if not tile_map.in_bounds(nx, ny):
                continue
            # Allow stepping ONTO goal tile even if a building (so we can enter doors)
            if (nx, ny) != goal and not tile_map.is_walkable(nx, ny):
                continue

            step_cost = 1.4142 if dx and dy else 1.0
            tentative = g[current] + step_cost
            if tentative < g.get((nx, ny), 1e18):
                came[(nx, ny)] = current
                g[(nx, ny)] = tentative
                f = tentative + heuristic((nx, ny), goal)
                heapq.heappush(open_set, (f, (nx, ny)))

    return None


def _reconstruct(came: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
    path = [current]
    while current in came:
        current = came[current]
        path.append(current)
    path.reverse()
    return path
