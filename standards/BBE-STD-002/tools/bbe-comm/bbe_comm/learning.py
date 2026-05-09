"""Self-optimization learning loop (RC2 §16.1, ADR-0001).

Append-only event log + suggestion synthesis. The loop NEVER mutates the
standard, the schema, the rules, or any policy. It only:
  - records observed events (with redacted content)
  - counts patterns over a sliding window
  - emits review-only suggestion files

REDACTION POLICY:
  - Never write raw block bodies, raw operator prompts, @hmac values,
    @nonce values, or any auth-only field value.
  - Content reduced to SHA-256 hashes plus structured metadata
    (check_id, type, label-shape, line counts).
  - Operator session names, correlation IDs are redacted to first 8 chars
    of their SHA-256.

EVENT TYPES (mandate-listed):
  lint_error, repair_suggestion, repeated_invalid_pattern,
  authorization_inference_attempt, missing_lineage, invalid_parent_id,
  legacy_tag_detected, guard_denial, operator_override, successful_repair,
  failed_repair, schema_gap_detected, test_gap_detected
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import PACKAGE_VERSION


EVENT_TYPES = {
    "lint_error",
    "repair_suggestion",
    "repeated_invalid_pattern",
    "authorization_inference_attempt",
    "missing_lineage",
    "invalid_parent_id",
    "legacy_tag_detected",
    "guard_denial",
    "operator_override",
    "successful_repair",
    "failed_repair",
    "schema_gap_detected",
    "test_gap_detected",
}

# The auth-only fields whose VALUES must never appear in the learning store.
_REDACTED_FIELD_VALUES = {
    "hmac", "nonce", "scope", "target", "issued_by",
    "not_after", "revokes",
    "x-bbe-sig", "x-bbe-ledger", "x-bbe-attest",
    # Redact correlation/parent ids partially — keep first 8 chars of hash
    # for grouping while losing the recoverable id.
}

# Suggestion-rate-limit: do not generate the same suggestion twice within N seconds
SUGGESTION_RATE_LIMIT_SECS = 86400  # 24h


def _hash(s: str) -> str:
    """Return first 12 hex chars of SHA-256(s) — enough to group, not enough to recover."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def _redact_correlation_id(corr: str | None) -> str | None:
    if not corr:
        return None
    return f"corr#{_hash(corr)}"


@dataclass
class LearningEvent:
    """One event in the append-only log."""
    schema_version: str = "1.0"
    bbe_comm_version: str = PACKAGE_VERSION
    timestamp: str = ""             # ISO-8601 UTC
    event_type: str = ""            # one of EVENT_TYPES
    check_id: str | None = None     # if event is a finding
    block_label_shape: str | None = None  # length-bucketed label shape, not the label itself
    block_type: str | None = None
    correlation_hash: str | None = None
    file_hash: str | None = None    # hash of file path (relative), not absolute
    summary: str = ""               # short, redacted human description
    severity: str | None = None     # error | warning | info
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _label_shape(label: str | None) -> str | None:
    if not label:
        return None
    bucket = ("short" if len(label) <= 16 else
              "medium" if len(label) <= 32 else
              "long")
    has_dash = "-" in label
    has_under = "_" in label
    return f"{bucket}|{'D' if has_dash else ''}{'U' if has_under else ''}"


class LearningStore:
    """Append-only JSONL store. No reads-then-rewrites. No deletes."""

    def __init__(self, store_dir: str | Path):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.store_dir / "learning-events.jsonl"
        self.suggestions_dir = self.store_dir / "suggestions"
        self.suggestions_dir.mkdir(parents=True, exist_ok=True)
        self.suggestion_marker_dir = self.store_dir / ".suggestion-markers"
        self.suggestion_marker_dir.mkdir(parents=True, exist_ok=True)

    def observe(self, event: LearningEvent) -> None:
        if event.event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type: {event.event_type!r}")
        if not event.timestamp:
            event.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # Final redaction safety net: scrub `extra` for forbidden keys
        for forbidden in _REDACTED_FIELD_VALUES:
            if forbidden in event.extra:
                event.extra[forbidden] = "<REDACTED>"
        with self.events_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def read_all(self) -> list[LearningEvent]:
        if not self.events_path.exists():
            return []
        out: list[LearningEvent] = []
        with self.events_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Tolerate forward-compatible schema versions
                evt = LearningEvent(**{k: v for k, v in d.items() if k in LearningEvent.__dataclass_fields__})
                out.append(evt)
        return out

    def _suggestion_marker(self, key: str) -> Path:
        return self.suggestion_marker_dir / f"{_hash(key)}.last"

    def _rate_limit(self, key: str) -> bool:
        """True if a suggestion of this key was emitted within the rate-limit window."""
        marker = self._suggestion_marker(key)
        if not marker.exists():
            return False
        last = float(marker.read_text().strip() or "0")
        return (time.time() - last) < SUGGESTION_RATE_LIMIT_SECS

    def _mark_suggested(self, key: str) -> None:
        self._suggestion_marker(key).write_text(str(time.time()))

    # --- Suggestion synthesis ---

    def synthesize_suggestions(self, min_count: int = 5) -> list[dict[str, Any]]:
        """Scan recent events and emit suggestions when patterns exceed thresholds.

        Returns a list of suggestion descriptors. Each is a dict with keys:
          target_file (path under suggestions/)
          title (short)
          body (text)
          rate_key (used for rate limiting)
        Also writes them to disk (append-only — does NOT overwrite).

        Rate-limited: same suggestion not re-emitted within 24h.
        """
        events = self.read_all()
        out: list[dict[str, Any]] = []

        # Pattern 1: same check_id firing >= min_count times → suggest a quick-fix doc
        check_counts: dict[str, int] = {}
        for e in events:
            if e.event_type == "lint_error" and e.check_id:
                check_counts[e.check_id] = check_counts.get(e.check_id, 0) + 1
        for cid, count in check_counts.items():
            if count < min_count:
                continue
            rate_key = f"check-frequent:{cid}"
            if self._rate_limit(rate_key):
                continue
            target = self.suggestions_dir / "operator-training.md"
            self._append_suggestion(target,
                title=f"Frequent {cid}",
                body=(
                    f"`{cid}` has fired {count} times in the recent learning window. "
                    f"Consider operator training material covering this rule, or a "
                    f"linter pre-commit hook in repos that emit this finding often.\n"
                    f"\nThis is a SUGGESTION ONLY. No spec, schema, or rule has been "
                    f"changed. Operator review required."
                ),
            )
            self._mark_suggested(rate_key)
            out.append({
                "target_file": str(target.relative_to(self.store_dir)),
                "title": f"Frequent {cid}",
                "rate_key": rate_key,
            })

        # Pattern 2: authorization_inference_attempt → suggest new test case
        infer_count = sum(1 for e in events if e.event_type == "authorization_inference_attempt")
        if infer_count >= 3 and not self._rate_limit("auth-inference-test"):
            target = self.suggestions_dir / "new-test-cases.md"
            self._append_suggestion(target,
                title="Anti-inference test expansion",
                body=(
                    f"Observed {infer_count} authorization-inference attempts. "
                    f"Consider expanding tests/test_incident_replay.py with the "
                    f"observed phrase variants. This is a SUGGESTION; the spec's "
                    f"§7.1 anti-inference list is the authoritative source."
                ),
            )
            self._mark_suggested("auth-inference-test")
            out.append({"target_file": str(target.relative_to(self.store_dir)),
                        "title": "Anti-inference test expansion",
                        "rate_key": "auth-inference-test"})

        # Pattern 3: legacy_tag_detected → suggest migration doc update
        legacy_count = sum(1 for e in events if e.event_type == "legacy_tag_detected")
        if legacy_count >= min_count and not self._rate_limit("migration-doc"):
            target = self.suggestions_dir / "process-improvements.md"
            self._append_suggestion(target,
                title="Legacy-tag migration adoption rate",
                body=(
                    f"Observed {legacy_count} legacy-tag detections. Operators may benefit "
                    f"from a `bbe-comm normalize` integration in the pre-commit hook of "
                    f"frequently-affected repos. Suggested for review."
                ),
            )
            self._mark_suggested("migration-doc")
            out.append({"target_file": str(target.relative_to(self.store_dir)),
                        "title": "Legacy-tag migration adoption rate",
                        "rate_key": "migration-doc"})

        # Pattern 4: failed_repair → suggest new linter rule
        failed_repair_count = sum(1 for e in events if e.event_type == "failed_repair")
        if failed_repair_count >= 5 and not self._rate_limit("new-linter-rules"):
            target = self.suggestions_dir / "new-linter-rules.md"
            self._append_suggestion(target,
                title="Recurring failed repairs",
                body=(
                    f"Observed {failed_repair_count} failed repair attempts. The patterns "
                    f"may indicate a missing linter rule or ambiguous spec text. Operator "
                    f"to review the `failed_repair` events and consider authoring a new "
                    f"BBE-COMM-NNN check or amending an existing rule's repair-suggest text."
                ),
            )
            self._mark_suggested("new-linter-rules")
            out.append({"target_file": str(target.relative_to(self.store_dir)),
                        "title": "Recurring failed repairs",
                        "rate_key": "new-linter-rules"})

        return out

    @staticmethod
    def _append_suggestion(target: Path, title: str, body: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with target.open("a", encoding="utf-8") as fp:
            fp.write(f"\n\n## PROPOSED — {title} ({ts})\n\n{body}\n")


# --- Convenience: build events from common bbe-comm contexts ---

def event_from_finding(finding, file_path: str | None = None) -> LearningEvent:
    return LearningEvent(
        event_type="lint_error",
        check_id=finding.check_id,
        severity=finding.severity,
        block_label_shape=_label_shape(getattr(finding, "block_label", None)),
        file_hash=_hash(file_path or "<input>"),
        summary=f"{finding.check_id} {finding.severity} at L{finding.line}",
    )


def event_from_incident(incident_result, file_path: str | None = None) -> LearningEvent:
    if incident_result.verdict != "pattern-without-auth":
        return LearningEvent(
            event_type="lint_error",
            summary=f"incident-test verdict: {incident_result.verdict}",
            file_hash=_hash(file_path or "<input>"),
        )
    return LearningEvent(
        event_type="authorization_inference_attempt",
        severity="error",
        summary=f"incident-test detected {len(incident_result.matches)} prose-only auth-inference cues",
        file_hash=_hash(file_path or "<input>"),
        extra={"match_count": len(incident_result.matches)},
    )
