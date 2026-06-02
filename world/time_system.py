"""
time_system.py — In-game time, day/night cycle, seasons.
"""

from __future__ import annotations
from dataclasses import dataclass

import config


@dataclass
class TimeSystem:
    """
    Tracks in-game time. 24 hours per day, 30 days per month, 4 months per year.
    """
    day: int = 1
    month: int = 1
    year: int = 1
    hour: float = 8.0   # start at 8 AM

    HOURS_PER_DAY: int = 24
    DAYS_PER_MONTH: int = 30
    MONTHS_PER_YEAR: int = 4

    MONTH_NAMES = ("Spring", "Summer", "Autumn", "Winter")

    def advance(self, dt_seconds: float) -> None:
        """Advance time by the given seconds of real time (already scaled)."""
        hours_per_sec = 1.0 / config.SECONDS_PER_HOUR
        self.hour += dt_seconds * hours_per_sec
        while self.hour >= self.HOURS_PER_DAY:
            self.hour -= self.HOURS_PER_DAY
            self.day += 1
            if self.day > self.DAYS_PER_MONTH:
                self.day = 1
                self.month += 1
                if self.month > self.MONTHS_PER_YEAR:
                    self.month = 1
                    self.year += 1

    @property
    def is_night(self) -> bool:
        return self.hour < config.DAYTIME_START_HOUR or self.hour >= config.NIGHTTIME_START_HOUR

    @property
    def is_day(self) -> bool:
        return not self.is_night

    def daylight_intensity(self) -> float:
        """0.0 = full dark, 1.0 = full daylight. Smooth ramp at dawn/dusk."""
        h = self.hour
        if h < 5 or h > 22:
            return 0.0
        if 7 <= h <= 19:
            return 1.0
        if h < 7:
            return (h - 5) / 2.0
        return (22 - h) / 3.0

    def format(self) -> str:
        am_pm = "AM" if self.hour < 12 else "PM"
        h12 = int(self.hour) % 12 or 12
        m = int((self.hour % 1) * 60)
        season = self.MONTH_NAMES[self.month - 1]
        return f"Y{self.year} · {season} · Day {self.day} · {h12:02d}:{m:02d} {am_pm}"

    def to_dict(self) -> dict:
        return {"day": self.day, "month": self.month, "year": self.year, "hour": self.hour}

    @classmethod
    def from_dict(cls, d: dict) -> "TimeSystem":
        return cls(day=d["day"], month=d["month"], year=d["year"], hour=d["hour"])
