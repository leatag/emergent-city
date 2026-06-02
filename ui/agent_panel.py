"""
agent_panel.py — Left-side inspector for the selected agent.

Click on the map -> if there's an agent under the cursor (within tolerance),
open the panel with their details. ESC closes. The panel exposes
`selected_agent_id` so main.py can implement camera-follow (F key).
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Tuple

import pygame

import config

if TYPE_CHECKING:
    from world.world import World
    from rendering.camera import Camera


class AgentPanel:
    WIDTH = 320
    PAD = 12
    LINE_H = 18

    def __init__(self, screen: pygame.Surface, world: "World", camera: "Camera") -> None:
        self.screen = screen
        self.world = world
        self.camera = camera
        self.font = pygame.font.SysFont("arial", 12)
        self.title_font = pygame.font.SysFont("arial", 14, bold=True)
        self.selected_agent_id: int = -1
        self.is_open: bool = False

    # ── Public API used by main.py ────────────────────────────────────────────
    def handle_click(self, pos: Tuple[int, int]) -> None:
        """Open panel if an agent is under the click."""
        tx, ty = self.camera.screen_to_tile(*pos)
        # Find nearest living agent within 1 tile of the clicked tile.
        best_id = -1
        best_d = 1.5  # squared-tile distance threshold (sqrt ~ 1.22)
        for a in self.world.agents:
            if not a.alive:
                continue
            d = (a.x - tx) ** 2 + (a.y - ty) ** 2
            if d <= best_d:
                best_d = d
                best_id = a.id
        if best_id != -1:
            self.selected_agent_id = best_id
            self.is_open = True
        else:
            self.close()

    def close(self) -> None:
        self.is_open = False
        # Keep selected_agent_id so "follow" still works after closing the panel.

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self) -> None:
        if not self.is_open:
            return
        agent = self.world.get_agent(self.selected_agent_id) if self.selected_agent_id != -1 else None
        if agent is None:
            self.is_open = False
            return

        w = self.WIDTH
        h = self.screen.get_height()
        x, y = 0, 0
        # Background
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((*config.PALETTE.ui_bg, 230))
        self.screen.blit(panel, (x, y))

        cur_y = y + self.PAD
        # Title
        title = self.title_font.render(f"{agent.name}  #{agent.id}", True, config.PALETTE.ui_accent)
        self.screen.blit(title, (x + self.PAD, cur_y))
        cur_y += 22

        lines = [
            f"Age: {agent.age}",
            f"Position: ({agent.x:.1f}, {agent.y:.1f})",
            f"Action: {agent.current_action}",
            f"Home: {agent.home_id}    Workplace: {agent.workplace_id}",
            f"Faction: {agent.faction_id}    Police: {agent.is_police}",
            f"Arrested ticks: {agent.arrested_ticks}",
            "",
            "NEEDS:",
        ]
        for line in lines:
            surf = self.font.render(line, True, config.PALETTE.ui_text)
            self.screen.blit(surf, (x + self.PAD, cur_y))
            cur_y += self.LINE_H

        # Needs bars
        needs = getattr(agent, "needs", None)
        if needs is not None:
            for name in ("hunger", "energy", "safety", "social", "meaning", "money", "belonging"):
                val = getattr(needs, name, None)
                if val is None:
                    continue
                self._draw_bar(x + self.PAD, cur_y, w - 2 * self.PAD, name, float(val))
                cur_y += self.LINE_H

        cur_y += 6
        if agent.last_thought:
            txt = f"Thought: {agent.last_thought[:60]}"
            surf = self.font.render(txt, True, config.PALETTE.ui_text_dim)
            self.screen.blit(surf, (x + self.PAD, cur_y))
            cur_y += self.LINE_H
        if agent.last_dialogue:
            txt = f"\"{agent.last_dialogue[:60]}\""
            surf = self.font.render(txt, True, config.PALETTE.ui_text_good)
            self.screen.blit(surf, (x + self.PAD, cur_y))
            cur_y += self.LINE_H

        # Footer hint
        hint = self.font.render("F follow   ESC close", True, config.PALETTE.ui_text_dim)
        self.screen.blit(hint, (x + self.PAD, h - 22))

    def _draw_bar(self, x: int, y: int, width: int, label: str, value: float) -> None:
        value = max(0.0, min(1.0, value))
        # Label
        text = self.font.render(label, True, config.PALETTE.ui_text)
        self.screen.blit(text, (x, y))
        # Bar background
        bar_x = x + 90
        bar_w = max(40, width - 100)
        bar_h = 8
        pygame.draw.rect(self.screen, (50, 50, 60), (bar_x, y + 4, bar_w, bar_h))
        # Bar fill — red when critical
        if value < config.NEED_CRITICAL_THRESHOLD:
            color = config.PALETTE.ui_text_danger
        elif value < config.NEED_LOW_THRESHOLD:
            color = (220, 180, 90)
        else:
            color = config.PALETTE.ui_text_good
        pygame.draw.rect(self.screen, color, (bar_x, y + 4, int(bar_w * value), bar_h))
