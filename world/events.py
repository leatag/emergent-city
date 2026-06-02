"""
events.py — World event log. Pumps the UI event feed and the LLM router.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from collections import deque
import time


@dataclass
class WorldEvent:
    """
    A noteworthy thing that happened. Importance 0..1 drives whether the LLM
    is consulted and whether the UI feed shows it.
    """
    kind: str               # "birth", "death", "crime", "fight", "love", ...
    actor_id: int
    target_id: int = -1
    location: tuple = (-1, -1)
    importance: float = 0.3
    timestamp: float = 0.0
    text: str = ""
    payload: Dict[str, Any] = None  # arbitrary structured payload

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.payload is None:
            self.payload = {}


class EventBus:
    """In-memory ring buffer of recent events. Other systems subscribe via poll."""

    def __init__(self, max_events: int = 2000):
        self.events: deque[WorldEvent] = deque(maxlen=max_events)
        self._listeners: List = []

    def post(self, event: WorldEvent) -> None:
        self.events.append(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

    def subscribe(self, callback) -> None:
        self._listeners.append(callback)

    def recent(self, n: int = 50) -> List[WorldEvent]:
        return list(self.events)[-n:]

    def filter(self, kind: Optional[str] = None, min_importance: float = 0.0) -> List[WorldEvent]:
        return [
            e for e in self.events
            if (kind is None or e.kind == kind) and e.importance >= min_importance
        ]
