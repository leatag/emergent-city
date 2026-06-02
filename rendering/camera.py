"""
camera.py — Isometric camera. Handles pan/zoom and the tile↔screen mapping.
"""

from __future__ import annotations
import config


class Camera:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0
        self.screen_w = config.SCREEN_WIDTH
        self.screen_h = config.SCREEN_HEIGHT

    # ── Movement ──────────────────────────────────────────────────────────────
    def pan(self, dx: float, dy: float) -> None:
        self.x += dx / self.zoom
        self.y += dy / self.zoom

    def zoom_at(self, factor: float, sx: float, sy: float) -> None:
        old_zoom = self.zoom
        self.zoom = max(config.CAMERA_MIN_ZOOM,
                        min(config.CAMERA_MAX_ZOOM, self.zoom * factor))
        # Keep the point under the cursor stable
        scale = self.zoom / old_zoom
        self.x = sx - (sx - self.x) * scale
        self.y = sy - (sy - self.y) * scale

    def center_on(self, tx: int, ty: int) -> None:
        sx, sy = self.tile_to_screen(tx, ty)
        self.x += self.screen_w / 2 - sx
        self.y += self.screen_h / 2 - sy

    # ── Transforms ────────────────────────────────────────────────────────────
    def tile_to_screen(self, tx: float, ty: float) -> tuple:
        tw = config.TILE_WIDTH * self.zoom
        th = config.TILE_HEIGHT * self.zoom
        sx = (tx - ty) * tw / 2 + self.x
        sy = (tx + ty) * th / 2 + self.y
        return sx, sy

    def screen_to_tile(self, sx: float, sy: float) -> tuple:
        tw = config.TILE_WIDTH * self.zoom
        th = config.TILE_HEIGHT * self.zoom
        sx -= self.x
        sy -= self.y
        tx = (sx / (tw / 2) + sy / (th / 2)) / 2
        ty = (sy / (th / 2) - sx / (tw / 2)) / 2
        return int(tx), int(ty)

    def resize(self, w: int, h: int) -> None:
        self.screen_w, self.screen_h = w, h
