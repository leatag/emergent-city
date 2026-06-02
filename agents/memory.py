"""
memory.py — Lightweight per-agent memory: recent events, salient people.
Used by the LLM layer when generating internal monologue or dialogue.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from collections import deque

import config


@dataclass
class MemoryEntry:
    kind: str
    text: str
    importance: float
    timestamp: float = 0.0
    other_id: int = -1


@dataclass
class AgentMemory:
    recent: deque = field(default_factory=lambda: deque(maxlen=config.AGENT_MEMORY_SIZE))
    salient_people: Dict[int, float] = field(default_factory=dict)  # id -> salience

    def remember(self, entry: MemoryEntry) -> None:
        self.recent.append(entry)
        if entry.other_id != -1:
            cur = self.salient_people.get(entry.other_id, 0.0)
            self.salient_people[entry.other_id] = min(1.0, cur + entry.importance * 0.3)

    def top_memories(self, k: int = 5) -> List[MemoryEntry]:
        return sorted(list(self.recent), key=lambda m: m.importance, reverse=True)[:k]

    def to_dict(self) -> dict:
        return {
            "recent": [
                {"kind": m.kind, "text": m.text, "imp": m.importance,
                 "ts": m.timestamp, "other": m.other_id}
                for m in self.recent
            ],
            "salient": {str(k): v for k, v in self.salient_people.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AgentMemory":
        am = cls()
        for m in d["recent"]:
            am.recent.append(MemoryEntry(
                kind=m["kind"], text=m["text"], importance=m["imp"],
                timestamp=m["ts"], other_id=m["other"]
            ))
        am.salient_people = {int(k): v for k, v in d["salient"].items()}
        return am
