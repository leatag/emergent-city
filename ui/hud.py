"""
hud.py — Top status bar: in-game clock, day, population, deaths, money supply,
faction counts, LLM stats.
"""

from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
from world.world import World


class HUD:
def __init__(self) -> None:
    self.font = pygame.font.SysFont("arial", 14, bold=True)
    self.small = pygame.font.SysFont("arial", 12)

def render(self, surf: pygame.Surface, world: "World", fps: float,
           llm_calls: int = 0, paused: bool = False, speed: float = 1.0) -> None:
    bar = pygame.Surface((surf.get_width(), 28), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 170))
    surf.blit(bar, (0, 0))

    ts = world.time_system
    alive = sum(1 for a in world.agents if a.alive)
    dead = sum(1 for a in world.agents if not a.alive)
    wanted = sum(1 for a in world.agents if a.alive and getattr(a, "wanted", False))

    line = (
        f"День {ts.day}  {ts.hour:02d}:{ts.minute:02d}  "
        f"Сезон: {ts.season_name}  "
        f"Население: {alive}  Смерти: {dead}  Розыск: {wanted}  "
        f"Группировки: {len(world.factions.factions)}  "
        f"FPS: {fps:.0f}  LLM: {llm_calls}"
    )
    if paused:
        line = "[ПАУЗА]  " + line
    elif speed != 1.0:
        line = f"[x{speed:.1f}]  " + line

    text = self.font.render(line, True, (240, 240, 240))
    surf.blit(text, (8, 6))
