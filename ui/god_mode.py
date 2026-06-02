"""
god_mode.py — A debug/cheat toggle. When active, draws a corner indicator.
Hooks can be wired later (spawn agents, set need values, ignite buildings).
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import pygame

import config

if TYPE_CHECKING:
from world.world import World


class GodMode:
def __init__(self, world: "World") -> None:
    self.world = world
    self.active: bool = False
    self.font = pygame.font.SysFont("arial", 13, bold=True)

def toggle(self) -> None:
    self.active = not self.active

def draw_indicator(self, screen: pygame.Surface) -> None:
    if not self.active:
        return
    text = self.font.render("✦ GOD MODE ✦", True, config.PALETTE.ui_accent)
    x = screen.get_width() // 2 - text.get_width() // 2
    y = 8
    # Background pill
    pad = 8
    bg = pygame.Surface((text.get_width() + pad * 2, text.get_height() + pad), pygame.SRCALPHA)
    bg.fill((*config.PALETTE.ui_bg, 200))
    screen.blit(bg, (x - pad, y - pad // 2))
    screen.blit(text, (x, y))
