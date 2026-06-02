"""
renderer.py — Top-down 2D tile, building, and agent rendering with a
day/night tint overlay. Pure pygame, no asset files.

API:
    r = Renderer(screen, world, camera)
    r.draw()
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict

import pygame

import config
from rendering.camera import Camera
from rendering.lighting import tint_for_hour, building_window_alpha
from world.tile_map import TileType
from world.buildings import BuildingType

if TYPE_CHECKING:
    from world.world import World


_TILE_COLORS: Dict[TileType, tuple] = {
    TileType.GRASS:      config.PALETTE.grass,
    TileType.GRASS_LUSH: config.PALETTE.grass_lush,
    TileType.ROAD:       config.PALETTE.road,
    TileType.SIDEWALK:   config.PALETTE.sidewalk,
    TileType.WATER:      config.PALETTE.water,
    TileType.PLAZA:      config.PALETTE.sidewalk,
    TileType.DIRT:       (110, 85, 55),
}

_BUILDING_COLORS: Dict[BuildingType, tuple] = {
    BuildingType.HOUSE:          config.PALETTE.house_wall,
    BuildingType.HOUSE_WEALTHY:  config.PALETTE.house_wealthy_wall,
    BuildingType.SHACK:          config.PALETTE.slum_wall,
    BuildingType.SHOP:           config.PALETTE.shop_wall,
    BuildingType.FACTORY:        config.PALETTE.factory_wall,
    BuildingType.BAR:            (140, 90, 130),
    BuildingType.PARK_BENCH:     (90, 60, 40),
    BuildingType.CHURCH:         (180, 170, 200),
    BuildingType.POLICE_STATION: (90, 110, 160),
}


class Renderer:
    def __init__(self, screen: pygame.Surface, world: "World", camera: Camera) -> None:
        self.screen = screen
        self.world = world
        self.camera = camera
        self.name_font = pygame.font.SysFont("arial", 10)
        # Selected agent id is owned by the AgentPanel; renderer reads from world if needed.
        self.selected_agent_id: int = -1

    # ── Public ────────────────────────────────────────────────────────────────
    def draw(self) -> None:
        self.screen.fill(config.PALETTE.background)
        self._draw_tiles()
        self._draw_buildings()
        self._draw_agents()
        self._draw_tint()

    # ── Tiles ─────────────────────────────────────────────────────────────────
    def _draw_tiles(self) -> None:
        tm = self.world.tile_map
        cam = self.camera
        tw = config.TILE_WIDTH * cam.zoom
        th = config.TILE_HEIGHT * cam.zoom

        x0, y0 = cam.screen_to_tile(0, 0)
        x1, y1 = cam.screen_to_tile(cam.screen_w, cam.screen_h)
        x0 = max(0, min(x0, x1) - 1)
        y0 = max(0, min(y0, y1) - 1)
        x1 = min(tm.width, max(x0, x1) + 2)
        y1 = min(tm.height, max(y0, y1) + 2)

        for x in range(x0, x1):
            for y in range(y0, y1):
                t = tm.tiles[x][y]
                sx, sy = cam.tile_to_screen(x, y)
                color = _TILE_COLORS.get(t.type, (100, 100, 100))
                if t.danger > 0.05:
                    r, g, b = color
                    color = (
                        min(255, int(r + 80 * t.danger)),
                        max(0, int(g - 50 * t.danger)),
                        max(0, int(b - 50 * t.danger)),
                    )
                pygame.draw.rect(self.screen, color, (int(sx), int(sy), int(tw) + 1, int(th) + 1))

    # ── Buildings ─────────────────────────────────────────────────────────────
    def _draw_buildings(self) -> None:
        cam = self.camera
        tw = config.TILE_WIDTH * cam.zoom
        th = config.TILE_HEIGHT * cam.zoom
        glow = building_window_alpha(self.world.time_system.hour)

        for b in self.world.buildings.buildings:
            sx, sy = cam.tile_to_screen(b.x, b.y)
            w_px = int(tw * b.w)
            h_px = int(th * b.h)
            if w_px <= 0 or h_px <= 0:
                continue
            base = _BUILDING_COLORS.get(b.type, (140, 120, 100))
            if b.on_fire:
                base = (220, 80, 40)
            # body
            pygame.draw.rect(self.screen, base, (int(sx), int(sy), w_px, h_px))
            # roof outline
            roof = tuple(max(0, min(255, c + 25)) for c in base)
            pygame.draw.rect(self.screen, roof, (int(sx), int(sy), w_px, h_px), 2)
            # lit windows at night
            if glow > 20 and w_px > 6 and h_px > 6:
                win = (255, 220, 120)
                pygame.draw.rect(self.screen, win, (int(sx) + 3, int(sy) + 3, 3, 3))
                if w_px > 12:
                    pygame.draw.rect(self.screen, win, (int(sx) + w_px - 6, int(sy) + 3, 3, 3))
                if h_px > 12:
                    pygame.draw.rect(self.screen, win, (int(sx) + 3, int(sy) + h_px - 6, 3, 3))

    # ── Agents ────────────────────────────────────────────────────────────────
    def _draw_agents(self) -> None:
        cam = self.camera
        tw = config.TILE_WIDTH * cam.zoom
        th = config.TILE_HEIGHT * cam.zoom
        r = max(2, int(3 * cam.zoom))

        for a in self.world.agents:
            if not a.alive:
                continue
            sx, sy = cam.tile_to_screen(a.x, a.y)
            cx = int(sx + tw / 2)
            cy = int(sy + th / 2)
            # shadow
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy + 1), r + 1)
            # body
            pygame.draw.circle(self.screen, a.color, (cx, cy), r)
            if a.is_police:
                pygame.draw.circle(self.screen, (60, 90, 220), (cx, cy), r, 1)
            if a.faction_id != -1 and a.faction_id in self.world.factions.factions:
                fc = self.world.factions.factions[a.faction_id].color
                pygame.draw.circle(self.screen, fc, (cx, cy), r + 1, 1)
            if a.id == self.selected_agent_id:
                pygame.draw.circle(self.screen, (255, 255, 100), (cx, cy), r + 3, 1)
                label = self.name_font.render(a.name, True, (255, 255, 200))
                self.screen.blit(label, (cx - label.get_width() // 2, cy - r - 14))
            if a.last_dialogue and a.speech_cooldown > 0:
                bubble = self.name_font.render(a.last_dialogue[:40], True, (240, 240, 240))
                self.screen.blit(bubble, (cx + r + 2, cy - r - 8))

    # ── Tint ──────────────────────────────────────────────────────────────────
    def _draw_tint(self) -> None:
        tint = tint_for_hour(self.world.time_system.hour)
        if not tint or len(tint) < 4:
            return
        r, g, b, a = tint
        if a <= 0:
            return
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((int(r), int(g), int(b), int(a)))
        self.screen.blit(overlay, (0, 0))
