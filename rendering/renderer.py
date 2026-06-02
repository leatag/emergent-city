"""
renderer.py — Isometric tile, building, and agent rendering with depth sort
and a day/night tint overlay. Pure pygame, no asset files — diamonds and
quads only.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

import config
from rendering.camera import Camera
from rendering.lighting import tint_for_hour, building_window_alpha
from world.tile import TileType

if TYPE_CHECKING:
    from world.world import World


TILE_COLORS = {
    TileType.GRASS:    (80, 130, 70),
    TileType.DIRT:     (110, 85, 55),
    TileType.ROAD:     (70, 70, 75),
    TileType.WATER:    (50, 90, 140),
    TileType.SAND:     (200, 180, 120),
    TileType.STONE:    (110, 110, 115),
    TileType.SIDEWALK: (140, 140, 140),
    TileType.PARK:     (60, 110, 60),
}


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 12)
        self.name_font = pygame.font.SysFont("arial", 10)

    def render(self, world: "World", camera: Camera, selected_agent_id: int = -1) -> None:
        self.screen.fill((20, 20, 28))
        self._render_tiles(world, camera)
        self._render_buildings(world, camera)
        self._render_agents(world, camera, selected_agent_id)
        self._render_tint(world)

    # ── Tiles ─────────────────────────────────────────────────────────────────
    def _render_tiles(self, world: "World", camera: Camera) -> None:
        tm = world.tile_map
        tw = config.TILE_WIDTH * camera.zoom
        th = config.TILE_HEIGHT * camera.zoom

        # Visible-tile culling
        top_left = camera.screen_to_tile(0, 0)
        bot_right = camera.screen_to_tile(camera.screen_w, camera.screen_h)
        x0 = max(0, min(top_left[0], bot_right[0]) - 4)
        y0 = max(0, min(top_left[1], bot_right[1]) - 4)
        x1 = min(tm.width, max(top_left[0], bot_right[0]) + 4)
        y1 = min(tm.height, max(top_left[1], bot_right[1]) + 4)

        for x in range(x0, x1):
            for y in range(y0, y1):
                t = tm.tiles[x][y]
                sx, sy = camera.tile_to_screen(x, y)
                color = TILE_COLORS.get(t.type, (100, 100, 100))
                if t.danger > 0.05:
                    r, g, b = color
                    color = (min(255, int(r + 80 * t.danger)),
                             max(0, int(g - 60 * t.danger)),
                             max(0, int(b - 60 * t.danger)))
                pygame.draw.polygon(self.screen, color, [
                    (sx,           sy + th / 2),
                    (sx + tw / 2,  sy),
                    (sx + tw,      sy + th / 2),
                    (sx + tw / 2,  sy + th),
                ])

    # ── Buildings ─────────────────────────────────────────────────────────────
    def _render_buildings(self, world: "World", camera: Camera) -> None:
        glow = building_window_alpha(world.time_system.hour_float)
        for b in sorted(world.buildings.buildings, key=lambda b: (b.x + b.y)):
            sx, sy = camera.tile_to_screen(b.x, b.y)
            tw = config.TILE_WIDTH * camera.zoom
            th = config.TILE_HEIGHT * camera.zoom
            h = config.BUILDING_HEIGHT_PX * camera.zoom * b.size_modifier
            top = [
                (sx, sy + th * b.h / 2 - h),
                (sx + tw * b.w / 2, sy - h),
                (sx + tw * (b.w + b.h) / 2, sy + th * b.w / 2 - h),
                (sx + tw * b.h / 2, sy + th * (b.w + b.h) / 2 - h),
            ]
            base_color = b.color
            roof_color = tuple(min(255, c + 30) for c in base_color)
            # Left wall
            pygame.draw.polygon(self.screen, tuple(max(0, c - 40) for c in base_color), [
                (sx, sy + th * b.h / 2),
                (sx + tw * b.h / 2, sy + th * (b.w + b.h) / 2),
                top[3], top[0],
            ])
            # Right wall
            pygame.draw.polygon(self.screen, base_color, [
                (sx + tw * b.h / 2, sy + th * (b.w + b.h) / 2),
                (sx + tw * (b.w + b.h) / 2, sy + th * b.w / 2),
                top[2], top[3],
            ])
            # Roof
            pygame.draw.polygon(self.screen, roof_color, top)

            # Lit windows at night
            if glow > 20:
                col = (255, 220, 120, glow)
                surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.rect(surf, col, surf.get_rect())
                self.screen.blit(surf, (top[3][0] + 4, top[3][1] + 4))
                self.screen.blit(surf, (top[3][0] + 16, top[3][1] + 4))

    # ── Agents ────────────────────────────────────────────────────────────────
    def _render_agents(self, world: "World", camera: Camera, selected_id: int) -> None:
        for a in world.agents:
            if not a.alive:
                continue
            sx, sy = camera.tile_to_screen(a.x, a.y)
            r = max(2, int(4 * camera.zoom))
            cx, cy = int(sx + config.TILE_WIDTH * camera.zoom / 2), int(sy + config.TILE_HEIGHT * camera.zoom / 2)
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy + 1), r + 1)
            pygame.draw.circle(self.screen, a.color, (cx, cy), r)
            if a.is_police:
                pygame.draw.circle(self.screen, (60, 90, 220), (cx, cy), r, 1)
            if a.faction_id != -1 and a.faction_id in world.factions.factions:
                fc = world.factions.factions[a.faction_id].color
                pygame.draw.circle(self.screen, fc, (cx, cy), r + 1, 1)
            if a.id == selected_id:
                pygame.draw.circle(self.screen, (255, 255, 100), (cx, cy), r + 3, 1)
                label = self.name_font.render(a.name, True, (255, 255, 200))
                self.screen.blit(label, (cx - label.get_width() // 2, cy - r - 14))
            if a.last_dialogue and a.speech_cooldown > 0:
                bubble = self.name_font.render(a.last_dialogue[:40], True, (240, 240, 240))
                self.screen.blit(bubble, (cx + r + 2, cy - r - 8))

    # ── Tint ──────────────────────────────────────────────────────────────────
    def _render_tint(self, world: "World") -> None:
        r, g, b, a = tint_for_hour(world.time_system.hour_float)
        if a <= 0:
            return
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()),
                                 pygame.SRCALPHA)
        overlay.fill((r, g, b, a))
        self.screen.blit(overlay, (0, 0))
