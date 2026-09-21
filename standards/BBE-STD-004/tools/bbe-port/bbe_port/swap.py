"""Swap check — incumbent vs. candidate (BBE-STD-004 §6)."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .constants import ALL_CAPABILITIES
from .manifest import Manifest
from .tasks import Task


def compare(incumbent: Manifest, candidate: Manifest, tasks: Sequence[Task] | None = None) -> Dict[str, Any]:
    lost = [c for c in ALL_CAPABILITIES if incumbent.capability(c) and not candidate.capability(c)]
    gained = [c for c in ALL_CAPABILITIES if candidate.capability(c) and not incumbent.capability(c)]
    context_delta = candidate.context_tokens - incumbent.context_tokens

    impact: Dict[str, Any] = {
        "corpus_size": 0,
        "blocked_tasks": [],
        "blocked_weight": 0,
        "total_weight": 0,
    }
    verdict = "degraded" if lost else "compatible"

    if tasks:
        from .runner import block_reason  # local import: avoids a cycle

        blocked = [(t, block_reason(t, candidate)) for t in tasks]
        blocked = [(t, reason) for t, reason in blocked if reason]
        impact = {
            "corpus_size": len(tasks),
            "blocked_tasks": [{"id": t.id, "reason": reason} for t, reason in blocked],
            "blocked_weight": sum(t.weight for t, _ in blocked),
            "total_weight": sum(t.weight for t in tasks),
        }
        if blocked:
            # Known work breaks: that outranks "some flag went missing".
            verdict = "incompatible"
        elif lost:
            # Capabilities lost, but nothing in the corpus depends on them.
            verdict = "degraded"

    return {
        "from": incumbent.id,
        "to": candidate.id,
        "capability_lost": lost,
        "capability_gained": gained,
        "context_delta": context_delta,
        "context_from": incumbent.context_tokens,
        "context_to": candidate.context_tokens,
        "sovereignty_delta": _sovereignty_delta(incumbent, candidate),
        "corpus_impact": impact,
        "verdict": verdict,
    }


def _sovereignty_delta(incumbent: Manifest, candidate: Manifest) -> Dict[str, Any]:
    """Informational, never part of the verdict.

    Whether moving from eu/self-hosted to a US SaaS is acceptable is a legal
    decision, not one this tool gets to make. It reports the change and stops.
    """
    before, after = incumbent.sovereignty, candidate.sovereignty
    delta: Dict[str, Any] = {}
    for key in ("data_region", "weights_portable", "runs_offline"):
        if before.get(key) != after.get(key):
            delta[key] = {"from": before.get(key), "to": after.get(key)}
    return delta
