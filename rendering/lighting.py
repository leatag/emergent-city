"""
lighting.py — Returns a tint colour + ambient alpha for the current
in-game hour. Used as a screen-space overlay after world rendering.
"""

from __future__ import annotations
import math
import config


def tint_for_hour(hour_float: float) -> tuple:
    """Return (r, g, b, a) tint to alpha-blend over the rendered frame."""
    # 0..24 → cycle. Peak day ~13, peak night ~1.
    phase = (hour_float - 6.0) / 24.0 * 2.0 * math.pi   # sunrise at 6
    light = (math.sin(phase) + 1.0) / 2.0  # 0..1
    # Day: warm, transparent. Night: deep blue, opaque.
    if light > 0.85:
        return (255, 240, 200, 0)
    if light > 0.6:
        # Afternoon
        return (255, 230, 180, 20)
    if light > 0.35:
        # Dusk / dawn
        return (255, 150, 90, 60)
    # Night
    a = int(120 + (1.0 - light) * 70)
    return (15, 20, 70, min(190, a))


def building_window_alpha(hour_float: float) -> int:
    """0..255 — how strongly building windows glow."""
    phase = (hour_float - 6.0) / 24.0 * 2.0 * math.pi
    light = (math.sin(phase) + 1.0) / 2.0
    return int((1.0 - light) * 220)
