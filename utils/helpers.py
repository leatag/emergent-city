"""helpers.py — Small reusable utilities."""

from __future__ import annotations
import math
import random
from typing import Iterable


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def chebyshev(a: tuple, b: tuple) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def manhattan(a: tuple, b: tuple) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclid(a: tuple, b: tuple) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def weighted_choice(rng: random.Random, weights: dict):
    total = sum(max(0.0, w) for w in weights.values())
    if total <= 0.0:
        return None
    r = rng.random() * total
    s = 0.0
    for k, w in weights.items():
        if w <= 0:
            continue
        s += w
        if s >= r:
            return k
    return next(iter(weights))


def normal_clamped(rng: random.Random, mean: float, sd: float,
                   lo: float = 0.0, hi: float = 1.0) -> float:
    return clamp(rng.gauss(mean, sd), lo, hi)


def chunks(seq, size: int) -> Iterable:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]
