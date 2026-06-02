"""
event_log.py — Bottom-left rolling list of recent world events
(deaths, fights, arrests, riots, friendships, romance, etc.)
"""

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.world import World


class EventLogUI:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont("arial", 12)

    def render(self, surf: pygame.Surface, world: "World", max_lines: int = 10) -> None:
        events = world.events.recent(max_lines)
        if not events:
            return
        w = 380
        h = 18 * len(events) + 8
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        x = 6
        y = surf.get_height() - h - 6
        surf.blit(bg, (x, y))

        for i, ev in enumerate(reversed(events)):
            color = self._color_for(ev.kind)
            text = self.font.render(f"[{ev.kind}] {ev.text[:50]}", True, color)
            surf.blit(text, (x + 6, y + 4 + i * 18))

    @staticmethod
    def _color_for(kind: str) -> tuple:
        return {
            "death":           (255, 100, 100),
            "crime":           (255, 160, 60),
            "arrest":          (120, 160, 255),
            "fight":           (255, 90, 90),
            "riot":            (255, 60, 60),
            "positive_social": (140, 230, 140),
            "romance":         (255, 160, 220),
            "faction_join":    (180, 140, 255),
            "faction_war":     (255, 70, 70),
        }.get(kind, (220, 220, 220))
