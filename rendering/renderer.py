"""
renderer.py — Top-down 2D tile, building, and agent rendering with a
day/night tint overlay. Pure pygame, no asset files.

Humans are drawn as composed shapes:
├ shadow (oval under feet)
├ legs (two rects, alternating per step phase)
├ body (torso rect, agent.color)
├ head (skin-tone circle)
└ facing indicator (small nose/cap dot in the facing direction)

API:
  r = Renderer(screen, world, camera)
  r.draw()
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Tuple

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

# Skin tone palette (varied per agent via id hash).
_SKIN_TONES: Tuple[Tuple[int, int, int], ...] = (
  (245, 213, 175),  # pale
  (228, 188, 152),
  (210, 169, 130),
  (188, 142, 100),
  (160, 112, 75),
  (130, 86, 55),
  (95, 62, 40),     # dark
)

# Hair tone palette.
_HAIR_TONES: Tuple[Tuple[int, int, int], ...] = (
  (30, 20, 15),     # black
  (75, 50, 30),     # brown
  (160, 110, 60),   # auburn
  (210, 180, 110),  # blond
  (180, 180, 180),  # gray
  (60, 40, 25),
)


def _skin_for(agent_id: int) -> Tuple[int, int, int]:
  return _SKIN_TONES[agent_id % len(_SKIN_TONES)]


def _hair_for(agent_id: int) -> Tuple[int, int, int]:
  return _HAIR_TONES[(agent_id * 7) % len(_HAIR_TONES)]


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

      # Camera now returns float coords — int() the corners for tile-range.
      x0f, y0f = cam.screen_to_tile(0, 0)
      x1f, y1f = cam.screen_to_tile(cam.screen_w, cam.screen_h)
      x0 = max(0, int(min(x0f, x1f)) - 1)
      y0 = max(0, int(min(y0f, y1f)) - 1)
      x1 = min(tm.width, int(max(x0f, x1f)) + 2)
      y1 = min(tm.height, int(max(y0f, y1f)) + 2)

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
      """Draw each agent as a tiny humanoid: legs + body + head + facing dot."""
      cam = self.camera
      tw = config.TILE_WIDTH * cam.zoom
      th = config.TILE_HEIGHT * cam.zoom

      # Scale figure parts by zoom. Sane minimums so distant agents stay visible.
      scale = max(0.6, cam.zoom)
      head_r = max(2, int(2.5 * scale))
      body_w = max(3, int(3 * scale))
      body_h = max(4, int(4 * scale))
      leg_w = max(1, int(1.4 * scale))
      leg_h = max(2, int(2 * scale))

      for a in self.world.agents:
          if not a.alive:
              continue
          sx, sy = cam.tile_to_screen(a.x, a.y)
          # Centre of the agent's tile.
          cx = int(sx + tw / 2)
          cy = int(sy + th / 2)

          skin = _skin_for(a.id)
          hair = _hair_for(a.id)

          # Layout: feet at cy+body_h//2+leg_h, body centered on cy, head above.
          feet_y = cy + body_h // 2
          body_top = cy - body_h // 2
          head_cy = body_top - head_r

          # Shadow (ellipse under the feet).
          shadow_w = body_w + 4
          shadow_h = max(2, int(body_h * 0.35))
          shadow_rect = pygame.Rect(
              cx - shadow_w // 2, feet_y + leg_h - shadow_h // 2,
              shadow_w, shadow_h,
          )
          shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
          pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect())
          self.screen.blit(shadow_surf, shadow_rect.topleft)

          # Legs — alternate forward/back based on step phase.
          step = int(a._step_phase) % 2 == 1 if hasattr(a, "_step_phase") else False
          left_x = cx - body_w // 2 + 1
          right_x = cx + body_w // 2 - leg_w - 1
          # Trouser colour: dark variant of body colour.
          trouser = tuple(max(0, int(c * 0.4)) for c in a.color)
          l_off = 1 if step else 0
          r_off = 0 if step else 1
          pygame.draw.rect(self.screen, trouser,
                           (left_x, feet_y + l_off, leg_w, leg_h))
          pygame.draw.rect(self.screen, trouser,
                           (right_x, feet_y + r_off, leg_w, leg_h))

          # Body (torso) — agent.color, with a subtle outline.
          body_rect = pygame.Rect(cx - body_w // 2, body_top, body_w, body_h)
          pygame.draw.rect(self.screen, a.color, body_rect)
          pygame.draw.rect(self.screen,
                           tuple(max(0, c - 40) for c in a.color),
                           body_rect, 1)

          # Head — skin tone circle with hair cap.
          pygame.draw.circle(self.screen, skin, (cx, head_cy), head_r)
          # Hair: top half of the head circle.
          hair_rect = pygame.Rect(cx - head_r, head_cy - head_r,
                                  head_r * 2, head_r)
          hair_surf = pygame.Surface((head_r * 2, head_r), pygame.SRCALPHA)
          pygame.draw.circle(hair_surf, hair, (head_r, head_r), head_r)
          self.screen.blit(hair_surf, hair_rect.topleft)

          # Facing indicator — small dot on the head in the facing direction.
          facing = getattr(a, "facing", "S")
          if facing == "N":
              fx, fy = cx, head_cy - head_r + 1
          elif facing == "S":
              fx, fy = cx, head_cy + head_r - 1
          elif facing == "E":
              fx, fy = cx + head_r - 1, head_cy
          else:  # "W"
              fx, fy = cx - head_r + 1, head_cy
          pygame.draw.circle(self.screen, (30, 20, 15), (fx, fy), max(1, head_r // 2))

          # Police hat / faction outline / selection ring on top.
          if a.is_police:
              hat = pygame.Rect(cx - head_r - 1, head_cy - head_r - 1,
                                head_r * 2 + 2, max(2, head_r // 2 + 1))
              pygame.draw.rect(self.screen, (40, 60, 140), hat)
              # Badge dot on chest
              pygame.draw.circle(self.screen, (255, 215, 0),
                                 (cx, cy), max(1, head_r // 2))

          if a.faction_id != -1 and a.faction_id in self.world.factions.factions:
              fc = self.world.factions.factions[a.faction_id].color
              ring_rect = body_rect.inflate(4, 4)
              pygame.draw.rect(self.screen, fc, ring_rect, 1)

          if a.id == self.selected_agent_id:
              sel_rect = pygame.Rect(cx - body_w, head_cy - head_r - 2,
                                     body_w * 2, body_h + head_r * 2 + leg_h + 6)
              pygame.draw.rect(self.screen, (255, 255, 100), sel_rect, 1)
              label = self.name_font.render(a.name, True, (255, 255, 200))
              self.screen.blit(
                  label,
                  (cx - label.get_width() // 2, head_cy - head_r - 16),
              )

          if a.last_dialogue and a.speech_cooldown > 0:
              bubble = self.name_font.render(a.last_dialogue[:40], True, (240, 240, 240))
              bx = cx + body_w
              by = head_cy - head_r - 4
              # Bubble background
              bg = pygame.Surface(
                  (bubble.get_width() + 6, bubble.get_height() + 4),
                  pygame.SRCALPHA,
              )
              bg.fill((0, 0, 0, 160))
              self.screen.blit(bg, (bx - 3, by - 2))
              self.screen.blit(bubble, (bx, by))

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
