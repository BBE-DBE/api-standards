"""Transports — how a gate run actually reaches a model.

The gate itself is transport-agnostic. `mock` is what CI uses: deterministic,
offline, no credentials. `openai_chat` is the live transport and covers both
hosted OpenAI-compatible APIs and self-hosted vLLM / llama.cpp servers, which
is what makes BBE-STD-004 §4.3 (deployment neutrality) real rather than
aspirational.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..manifest import Manifest


class TransportError(RuntimeError):
    """Transport could not produce a completion. Never a task failure.

    A transport error means the measurement did not happen. Scoring it as a
    failed task would let a broken fixture or an unreachable endpoint look
    like a quality problem.
    """


@dataclass
class Completion:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class Transport(Protocol):
    name: str

    def complete(self, manifest: Manifest, system: str | None, prompt: str, task_id: str) -> Completion:
        ...


def get_transport(name: str, **kwargs) -> Transport:
    if name == "mock":
        from .mock import MockTransport
        return MockTransport(**kwargs)
    if name == "openai_chat":
        from .openai_chat import OpenAIChatTransport
        return OpenAIChatTransport(**kwargs)
    raise TransportError(f"unknown transport: {name!r} (have: mock, openai_chat)")
