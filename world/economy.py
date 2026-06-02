"""
economy.py — Goods, prices, supply/demand. Updated daily.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict
import random

import config


@dataclass
class Economy:
    rng: random.Random
    prices: Dict[str, float] = field(default_factory=dict)
    supply: Dict[str, float] = field(default_factory=dict)
    demand: Dict[str, float] = field(default_factory=dict)
    inflation: float = 1.0

    def __post_init__(self) -> None:
        if not self.prices:
            for good, base in config.GOOD_BASE_PRICES.items():
                self.prices[good] = base
                self.supply[good] = 100.0
                self.demand[good] = 100.0

    # ── Trading ───────────────────────────────────────────────────────────────
    def price_of(self, good: str) -> float:
        return self.prices.get(good, 1.0) * self.inflation

    def record_purchase(self, good: str, quantity: float = 1.0) -> None:
        self.supply[good] = max(0.0, self.supply.get(good, 0.0) - quantity)
        self.demand[good] = self.demand.get(good, 0.0) + quantity * 0.5

    def record_production(self, good: str, quantity: float = 1.0) -> None:
        self.supply[good] = self.supply.get(good, 0.0) + quantity

    # ── Daily update ──────────────────────────────────────────────────────────
    def daily_tick(self) -> None:
        for good in self.prices:
            s = self.supply[good]
            d = self.demand[good]
            ratio = (d + 1.0) / (s + 1.0)
            sensitivity = config.SUPPLY_PRICE_SENSITIVITY
            # Move price toward demand/supply ratio
            target = config.GOOD_BASE_PRICES[good] * ratio ** sensitivity
            self.prices[good] += (target - self.prices[good]) * 0.25

            # Random walk noise
            self.prices[good] *= 1.0 + (self.rng.random() - 0.5) * config.PRICE_VOLATILITY

            # Decay supply/demand toward equilibrium
            self.supply[good] = max(10.0, self.supply[good] * 0.92 + 50.0 * 0.08)
            self.demand[good] = max(10.0, self.demand[good] * 0.92 + 50.0 * 0.08)

        # Mild inflation drift
        self.inflation *= 1.0 + (self.rng.random() - 0.48) * 0.002

    # ── Persistence ───────────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "prices": dict(self.prices),
            "supply": dict(self.supply),
            "demand": dict(self.demand),
            "inflation": self.inflation,
        }

    @classmethod
    def from_dict(cls, d: dict, rng: random.Random) -> "Economy":
        e = cls(rng=rng)
        e.prices = dict(d["prices"])
        e.supply = dict(d["supply"])
        e.demand = dict(d["demand"])
        e.inflation = d["inflation"]
        return e
