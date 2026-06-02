"""
prompts.py — Builds system+user prompts for LLM calls.
All system prompts are in Russian to keep generated text in-style.
"""

from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.agent import Agent
    from world.world import World


SYSTEM_ROLEPLAY = (
    "Ты — житель эмерджентного города. Отвечай коротко, на русском языке, "
    "от первого лица. Реплика — одно-два предложения, не более 25 слов. "
    "Соответствуй характеру и текущему состоянию персонажа."
)

SYSTEM_THOUGHT = (
    "Ты — внутренний монолог жителя города. Одна короткая мысль "
    "(до 12 слов) на русском языке, без кавычек."
)

SYSTEM_DECISION = (
    "Ты подсказываешь действие персонажу. Ответ — одно слово из списка: "
    "{actions}. Никаких пояснений."
)


def _agent_brief(a: "Agent") -> str:
    pers = a.personality
    n = a.needs
    traits = ", ".join(pers.unique_traits) or "—"
    return (
        f"Имя: {a.name}, возраст {a.age}.\n"
        f"Характер: O={pers.openness:.2f} C={pers.conscientiousness:.2f} "
        f"E={pers.extraversion:.2f} A={pers.agreeableness:.2f} N={pers.neuroticism:.2f}. "
        f"Черты: {traits}.\n"
        f"Состояние: голод={n.hunger:.2f}, силы={n.energy:.2f}, "
        f"безопасность={n.safety:.2f}, общение={n.social:.2f}, "
        f"смысл={n.meaning:.2f}, деньги={n.money:.0f}."
    )


def build_dialogue_prompt(a: "Agent", other: "Agent", context: str = "") -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_ROLEPLAY},
        {"role": "user", "content": (
            f"{_agent_brief(a)}\n"
            f"Ты разговариваешь с человеком по имени {other.name}.\n"
            f"Контекст: {context or 'случайная встреча на улице'}.\n"
            "Что ты ему скажешь?"
        )},
    ]


def build_thought_prompt(a: "Agent", world: "World") -> List[Dict[str, str]]:
    hour = world.time_system.hour
    return [
        {"role": "system", "content": SYSTEM_THOUGHT},
        {"role": "user", "content": (
            f"{_agent_brief(a)}\n"
            f"Сейчас {hour:02d}:00. Ты делаешь: {a.current_action}.\n"
            "Какая мысль у тебя в голове прямо сейчас?"
        )},
    ]


def build_decision_prompt(a: "Agent", world: "World", actions: List[str]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_DECISION.format(actions=", ".join(actions))},
        {"role": "user", "content": (
            f"{_agent_brief(a)}\n"
            f"Час: {world.time_system.hour}. Что разумно делать сейчас?"
        )},
    ]
