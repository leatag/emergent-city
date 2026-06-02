"""
personality.py — Big Five + unique trait pool. Drives behavior weights.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import random

import config


@dataclass
class Personality:
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    unique_traits: List[str] = field(default_factory=list)

    @classmethod
    def random(cls, rng: random.Random) -> "Personality":
        def b5() -> float:
            v = rng.gauss(config.BIG_FIVE_MEAN, config.BIG_FIVE_STDDEV)
            return max(0.05, min(0.95, v))
        traits = rng.sample(config.UNIQUE_TRAITS, k=rng.randint(2, 4))
        return cls(
            openness=b5(),
            conscientiousness=b5(),
            extraversion=b5(),
            agreeableness=b5(),
            neuroticism=b5(),
            unique_traits=traits,
        )

    def has(self, trait: str) -> bool:
        return trait in self.unique_traits

    def crime_propensity(self) -> float:
        """How likely to consider crime when desperate."""
        base = (1.0 - self.agreeableness) * 0.5 + self.neuroticism * 0.3
        if self.has("cruel"):
            base += 0.25
        if self.has("manipulative"):
            base += 0.15
        if self.has("vengeful"):
            base += 0.10
        if self.has("kind"):
            base -= 0.30
        if self.has("religious"):
            base -= 0.15
        return max(0.0, min(1.0, base))

    def social_drive(self) -> float:
        base = self.extraversion
        if self.has("awkward"):
            base -= 0.2
        if self.has("charismatic"):
            base += 0.2
        return max(0.0, min(1.0, base))

    def work_ethic(self) -> float:
        base = self.conscientiousness
        if self.has("lazy"):
            base -= 0.3
        if self.has("ambitious") or self.has("disciplined"):
            base += 0.25
        return max(0.0, min(1.0, base))

    def faith(self) -> float:
        if self.has("religious"):
            return 0.85
        if self.has("skeptical") or self.has("cynical"):
            return 0.10
        return 0.4 + (self.openness - 0.5) * 0.2

    def to_dict(self) -> dict:
        return {
            "o": self.openness, "c": self.conscientiousness,
            "e": self.extraversion, "a": self.agreeableness,
            "n": self.neuroticism, "traits": list(self.unique_traits),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Personality":
        return cls(openness=d["o"], conscientiousness=d["c"],
                   extraversion=d["e"], agreeableness=d["a"],
                   neuroticism=d["n"], unique_traits=list(d["traits"]))
