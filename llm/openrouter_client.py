"""
openrouter_client.py — Thin wrapper around OpenRouter's chat-completions API.
Async-friendly via threads; budget-tracked; auto-fallback between models.
"""

from __future__ import annotations
import os
import time
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, Future

import requests

import config


@dataclass
class LLMResponse:
    text: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    error: Optional[str] = None


class OpenRouterClient:
    """Synchronous-but-pooled client. Use submit() for fire-and-forget."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.pool = ThreadPoolExecutor(max_workers=config.LLM_POOL_SIZE)
        self.total_calls = 0
        self.total_tokens = 0
        self.failures = 0

    @property
    def enabled(self) -> bool:
        return bool(self.api_key) and config.LLM_ENABLED

    def submit(self, messages: List[Dict[str, str]],
               model: Optional[str] = None,
               max_tokens: int = 200,
               temperature: float = 0.85) -> Future:
        return self.pool.submit(self.complete, messages, model, max_tokens, temperature)

    def complete(self, messages: List[Dict[str, str]],
                 model: Optional[str] = None,
                 max_tokens: int = 200,
                 temperature: float = 0.85) -> LLMResponse:
        if not self.enabled:
            return LLMResponse(text="", model="disabled", error="LLM disabled")

        models_to_try = [model] if model else list(config.LLM_MODELS)
        last_err = None

        for m in models_to_try:
            if not m:
                continue
            t0 = time.time()
            try:
                resp = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/leatag/emergent-city",
                        "X-Title": "Emergent City",
                    },
                    json={
                        "model": m,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                    timeout=config.LLM_TIMEOUT_SECONDS,
                )
                latency = (time.time() - t0) * 1000.0
                if resp.status_code != 200:
                    last_err = f"{resp.status_code}: {resp.text[:200]}"
                    self.failures += 1
                    continue
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                usage = data.get("usage", {})
                self.total_calls += 1
                self.total_tokens += usage.get("total_tokens", 0)
                return LLMResponse(
                    text=text, model=m,
                    tokens_in=usage.get("prompt_tokens", 0),
                    tokens_out=usage.get("completion_tokens", 0),
                    latency_ms=latency,
                )
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
                self.failures += 1
                continue

        return LLMResponse(text="", model="failed", error=last_err or "no models")

    def shutdown(self) -> None:
        self.pool.shutdown(wait=False)
