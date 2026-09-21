"""Golden-corpus loading, hashing and mechanical checks (BBE-STD-004 §5)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from .constants import (
    ALL_CAPABILITIES,
    CHECK_TYPES,
    TASK_OPTIONAL_FIELDS,
    TASK_REQUIRED_FIELDS,
    TASK_VERSION,
)
from .manifest import Finding

TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_FENCE_RE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL)


@dataclass
class Task:
    raw: Dict[str, Any]
    source: str = ""

    @property
    def id(self) -> str:
        return str(self.raw.get("id", ""))

    @property
    def weight(self) -> int:
        return int(self.raw.get("weight", 1))

    @property
    def category(self) -> str:
        return str(self.raw.get("category", ""))

    @property
    def prompt(self) -> str:
        return str(self.raw.get("prompt", ""))

    @property
    def system(self) -> str | None:
        value = self.raw.get("system")
        return str(value) if isinstance(value, str) else None

    @property
    def requires(self) -> Tuple[str, ...]:
        value = self.raw.get("requires") or []
        return tuple(str(v) for v in value)

    @property
    def min_context_tokens(self) -> int:
        return int(self.raw.get("min_context_tokens", 0))

    @property
    def checks(self) -> List[Dict[str, Any]]:
        value = self.raw.get("checks")
        return list(value) if isinstance(value, list) else []


def validate_task(raw: Any, source: str = "") -> List[Finding]:
    findings: List[Finding] = []
    if not isinstance(raw, dict):
        return [Finding("BBE-TASK-002", "task must be a JSON object", source)]

    if raw.get("task_version") != TASK_VERSION:
        findings.append(
            Finding("BBE-TASK-001", f"task_version must be {TASK_VERSION!r}, got {raw.get('task_version')!r}", source)
        )

    for name in TASK_REQUIRED_FIELDS:
        if name not in raw:
            findings.append(Finding("BBE-TASK-002", f"required field missing: {name}", source))

    known = set(TASK_REQUIRED_FIELDS) | set(TASK_OPTIONAL_FIELDS)
    for name in raw:
        if name not in known:
            findings.append(Finding("BBE-TASK-002", f"unknown field: {name}", source))

    ident = raw.get("id")
    if "id" in raw and (not isinstance(ident, str) or not TASK_ID_RE.match(ident)):
        findings.append(Finding("BBE-TASK-003", f"id must be kebab-case, got {ident!r}", source))

    weight = raw.get("weight")
    if "weight" in raw and (not isinstance(weight, int) or isinstance(weight, bool) or not 1 <= weight <= 10):
        findings.append(Finding("BBE-TASK-002", f"weight must be an integer 1..10, got {weight!r}", source))

    for name in raw.get("requires") or []:
        if name not in ALL_CAPABILITIES:
            findings.append(Finding("BBE-TASK-005", f"unknown capability in requires[]: {name}", source))

    checks = raw.get("checks")
    if not isinstance(checks, list) or not checks:
        if "checks" in raw:
            findings.append(Finding("BBE-TASK-004", "checks must be a non-empty array", source))
    else:
        for index, check in enumerate(checks):
            findings.extend(_validate_check(check, index, source))

    return findings


def _validate_check(check: Any, index: int, source: str) -> List[Finding]:
    where = f"checks[{index}]"
    if not isinstance(check, dict):
        return [Finding("BBE-TASK-004", f"{where} must be an object", source)]

    kind = check.get("type")
    if kind not in CHECK_TYPES:
        return [Finding("BBE-TASK-004", f"{where} unknown type {kind!r}", source)]

    findings: List[Finding] = []
    if kind in ("contains_all", "contains_any", "not_contains"):
        values = check.get("values")
        if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
            findings.append(Finding("BBE-TASK-004", f"{where} ({kind}) needs a non-empty string array 'values'", source))
    elif kind == "json_has_keys":
        keys = check.get("keys")
        if not isinstance(keys, list) or not keys or not all(isinstance(k, str) for k in keys):
            findings.append(Finding("BBE-TASK-004", f"{where} (json_has_keys) needs a non-empty string array 'keys'", source))
    elif kind == "regex":
        pattern = check.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            findings.append(Finding("BBE-TASK-004", f"{where} (regex) needs a non-empty 'pattern'", source))
        else:
            try:
                re.compile(pattern)
            except re.error as exc:
                findings.append(Finding("BBE-TASK-004", f"{where} (regex) does not compile: {exc}", source))
    elif kind == "equals_normalized":
        if not isinstance(check.get("value"), str):
            findings.append(Finding("BBE-TASK-004", f"{where} (equals_normalized) needs a string 'value'", source))
    return findings


def load_corpus(directory: str | Path) -> Tuple[List[Task], List[Finding]]:
    """Load every *.json task under `directory`, sorted by id."""
    d = Path(directory)
    if not d.is_dir():
        return [], [Finding("BBE-TASK-002", f"corpus directory not found: {d}", str(d))]

    tasks: List[Task] = []
    findings: List[Finding] = []
    seen: Dict[str, str] = {}

    for path in sorted(d.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("BBE-TASK-002", f"malformed JSON: {exc}", path.name))
            continue
        task_findings = validate_task(raw, source=path.name)
        findings.extend(task_findings)
        if task_findings:
            continue
        task = Task(raw=raw, source=str(path))
        if task.id in seen:
            findings.append(
                Finding("BBE-TASK-006", f"duplicate task id {task.id!r} (also in {seen[task.id]})", path.name)
            )
            continue
        seen[task.id] = path.name
        tasks.append(task)

    tasks.sort(key=lambda t: t.id)
    return tasks, findings


def corpus_hash(tasks: Sequence[Task]) -> str:
    """Stable sha256 over the corpus.

    Reports are only comparable at equal hash (§7.3), so this must not depend
    on file names, ordering on disk, or key order inside a task.
    """
    hasher = hashlib.sha256()
    for task in sorted(tasks, key=lambda t: t.id):
        canonical = json.dumps(task.raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        hasher.update(task.id.encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(canonical.encode("utf-8"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


# --- mechanical checks -----------------------------------------------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower().rstrip(".!? ")


def _extract_json(text: str) -> Any:
    """Best-effort JSON extraction from model output.

    Models wrap JSON in prose or fences more often than not. Being lenient
    here measures the model's data, not its packaging; a task that must reject
    prose should add an explicit `not_contains` check.
    """
    candidates: List[str] = []
    fence = _FENCE_RE.search(text)
    if fence:
        candidates.append(fence.group(1))
    stripped = text.strip()
    candidates.append(stripped)
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end > start:
        candidates.append(stripped[start:end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def run_check(check: Dict[str, Any], text: str) -> Tuple[bool, str]:
    """Evaluate one check against model output. Returns (passed, description)."""
    kind = check["type"]
    haystack = text.lower()

    if kind == "contains_all":
        missing = [v for v in check["values"] if v.lower() not in haystack]
        return (not missing), f"contains_all missing {missing}" if missing else "contains_all"
    if kind == "contains_any":
        hit = any(v.lower() in haystack for v in check["values"])
        return hit, "contains_any" if hit else f"contains_any none of {check['values']}"
    if kind == "not_contains":
        present = [v for v in check["values"] if v.lower() in haystack]
        return (not present), f"not_contains found {present}" if present else "not_contains"
    if kind == "regex":
        hit = re.search(check["pattern"], text, re.MULTILINE | re.DOTALL) is not None
        return hit, "regex" if hit else f"regex no match: {check['pattern']}"
    if kind == "json_has_keys":
        payload = _extract_json(text)
        if not isinstance(payload, dict):
            return False, "json_has_keys: output is not a JSON object"
        missing = [k for k in check["keys"] if k not in payload]
        return (not missing), f"json_has_keys missing {missing}" if missing else "json_has_keys"
    if kind == "equals_normalized":
        hit = _normalize(text) == _normalize(check["value"])
        return hit, "equals_normalized" if hit else "equals_normalized mismatch"

    return False, f"unsupported check type {kind!r}"
