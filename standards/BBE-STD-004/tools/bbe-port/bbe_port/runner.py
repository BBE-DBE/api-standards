"""Gate runner and scoring (BBE-STD-004 §5, §7)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from .constants import MAX_EXCERPT_CHARS, REPORT_VERSION
from .manifest import Manifest
from .tasks import Task, corpus_hash, run_check
from .transports import Transport, TransportError


@dataclass
class TaskResult:
    id: str
    outcome: str  # passed | failed | blocked
    weight: int
    reason: str = ""
    failed_checks: List[str] = field(default_factory=list)
    excerpt: str = ""


def block_reason(task: Task, manifest: Manifest) -> str:
    """Why this task cannot be measured on this provider — '' if it can.

    A capability the provider does not have is a known limitation, not a
    quality signal (§5.3). Blocked tasks leave the denominator so a provider
    cannot raise its score by being incapable.
    """
    missing = [flag for flag in task.requires if not manifest.capability(flag)]
    if missing:
        return f"provider lacks capability: {', '.join(sorted(missing))}"
    if task.min_context_tokens and task.min_context_tokens > manifest.context_tokens:
        return (
            f"task needs {task.min_context_tokens} context tokens, "
            f"provider offers {manifest.context_tokens}"
        )
    return ""


def run_task(task: Task, manifest: Manifest, transport: Transport) -> tuple[TaskResult, int, int]:
    reason = block_reason(task, manifest)
    if reason:
        return TaskResult(id=task.id, outcome="blocked", weight=task.weight, reason=reason), 0, 0

    completion = transport.complete(
        manifest=manifest, system=task.system, prompt=task.prompt, task_id=task.id
    )

    failed: List[str] = []
    for check in task.checks:
        passed, description = run_check(check, completion.text)
        if not passed:
            failed.append(description)

    result = TaskResult(
        id=task.id,
        outcome="passed" if not failed else "failed",
        weight=task.weight,
        failed_checks=failed,
        # §7.3: excerpt only. Full transcripts belong in the audit store.
        excerpt="" if not failed else completion.text[:MAX_EXCERPT_CHARS],
    )
    return result, completion.input_tokens, completion.output_tokens


def verdict_for(score: float, floor: float, blocked_weight: int) -> str:
    if score < floor:
        return "NOT_QUALIFIED"
    return "QUALIFIED_DEGRADED" if blocked_weight > 0 else "QUALIFIED"


def run_corpus(
    tasks: Sequence[Task],
    manifest: Manifest,
    transport: Transport,
    floor: float,
) -> Dict[str, Any]:
    """Execute the corpus and build a report per portability-report.schema.json."""
    started = time.monotonic()
    results: List[TaskResult] = []
    input_tokens = output_tokens = 0

    for task in tasks:
        result, used_in, used_out = run_task(task, manifest, transport)
        results.append(result)
        input_tokens += used_in
        output_tokens += used_out

    passed = [r for r in results if r.outcome == "passed"]
    failed = [r for r in results if r.outcome == "failed"]
    blocked = [r for r in results if r.outcome == "blocked"]

    passed_weight = sum(r.weight for r in passed)
    scored_weight = passed_weight + sum(r.weight for r in failed)
    blocked_weight = sum(r.weight for r in blocked)

    # No measurable task: report 0.0 rather than dividing by zero. An
    # all-blocked corpus is a failure of the swap, not a perfect score.
    score = (passed_weight / scored_weight) if scored_weight else 0.0

    return {
        "report_version": REPORT_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_id": manifest.id,
        "transport": getattr(transport, "name", "unknown"),
        "corpus_hash": corpus_hash(tasks),
        "corpus_size": len(tasks),
        "floor": floor,
        "score": round(score, 4),
        "verdict": verdict_for(score, floor, blocked_weight),
        "totals": {
            "passed": len(passed),
            "failed": len(failed),
            "blocked": len(blocked),
            "passed_weight": passed_weight,
            "scored_weight": scored_weight,
            "blocked_weight": blocked_weight,
        },
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "wall_ms": int((time.monotonic() - started) * 1000),
        },
        "tasks": [
            {
                key: value
                for key, value in (
                    ("id", r.id),
                    ("outcome", r.outcome),
                    ("weight", r.weight),
                    ("reason", r.reason),
                    ("failed_checks", r.failed_checks),
                    ("excerpt", r.excerpt),
                )
                if value or key in ("id", "outcome", "weight")
            }
            for r in results
        ],
    }
