"""Provider-manifest loading and validation (BBE-STD-004 §4.2, §4.4)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .constants import (
    ALL_CAPABILITIES,
    DEPLOYMENTS,
    MANIFEST_OPTIONAL_FIELDS,
    MANIFEST_REQUIRED_FIELDS,
    MANIFEST_VERSION,
    REQUIRED_CAPABILITIES,
    ROLES,
    SOVEREIGNTY_REQUIRED_FIELDS,
    WIRES,
)

ID_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)/([A-Za-z0-9][A-Za-z0-9._-]*)$")
CREDENTIAL_REF_RE = re.compile(r"^(vault://[A-Za-z0-9/_.-]+|env:[A-Z][A-Z0-9_]*)$")
ENDPOINT_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Fail-closed secret sniffing. Deliberately broad: a false positive costs a
# rename, a false negative commits a key to git.
SECRET_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*\S{12,}"),
    re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),  # bare base64 blob
    re.compile(r"^[0-9a-f]{40,}$"),             # bare hex blob
)


@dataclass
class Finding:
    check_id: str
    message: str
    source: str = ""

    def __str__(self) -> str:  # pragma: no cover - formatting only
        where = f"{self.source}: " if self.source else ""
        return f"{where}{self.check_id} — {self.message}"


@dataclass
class Manifest:
    """A validated provider manifest.

    `raw` stays available because the swap check reports on fields the
    dataclass does not promote.
    """

    raw: Dict[str, Any]
    source: str = ""

    @property
    def id(self) -> str:
        return str(self.raw.get("id", ""))

    @property
    def role(self) -> str:
        return str(self.raw.get("role", ""))

    @property
    def deployment(self) -> str:
        return str(self.raw.get("deployment", ""))

    @property
    def wire(self) -> str:
        return str(self.raw.get("wire", ""))

    @property
    def context_tokens(self) -> int:
        return int(self.raw.get("context_tokens", 0))

    @property
    def max_output_tokens(self) -> int:
        return int(self.raw.get("max_output_tokens", 0))

    @property
    def credential_ref(self) -> str:
        return str(self.raw.get("credential_ref", ""))

    @property
    def endpoint_env(self) -> str:
        return str(self.raw.get("endpoint_env", ""))

    @property
    def sovereignty(self) -> Dict[str, Any]:
        sov = self.raw.get("sovereignty")
        return sov if isinstance(sov, dict) else {}

    def capability(self, name: str) -> bool:
        """Capability lookup. Absent optional flags read as False.

        Reading absent-as-False is the safe direction: it can only make a
        provider look less capable, never more.
        """
        caps = self.raw.get("capabilities")
        if not isinstance(caps, dict):
            return False
        return bool(caps.get(name, False))

    def capabilities(self) -> Dict[str, bool]:
        return {name: self.capability(name) for name in ALL_CAPABILITIES}


def _walk_strings(node: Any, path: str = "") -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    if isinstance(node, str):
        out.append((path, node))
    elif isinstance(node, dict):
        for key, value in node.items():
            out.extend(_walk_strings(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            out.extend(_walk_strings(value, f"{path}[{index}]"))
    return out


def _validate_capabilities(raw: Dict[str, Any], findings: List[Finding], source: str) -> None:
    caps = raw.get("capabilities")
    if not isinstance(caps, dict):
        findings.append(Finding("BBE-PORT-005", "capabilities must be an object", source))
        return
    for name in REQUIRED_CAPABILITIES:
        if name not in caps:
            findings.append(
                Finding("BBE-PORT-005", f"required capability flag missing: {name}", source)
            )
    for name, value in caps.items():
        if name not in ALL_CAPABILITIES:
            findings.append(Finding("BBE-PORT-005", f"unknown capability: {name}", source))
        elif not isinstance(value, bool):
            findings.append(
                Finding("BBE-PORT-005", f"capability {name} must be boolean, got {type(value).__name__}", source)
            )


def _validate_sovereignty(raw: Dict[str, Any], findings: List[Finding], source: str) -> None:
    sov = raw.get("sovereignty")
    if not isinstance(sov, dict):
        findings.append(Finding("BBE-PORT-006", "sovereignty must be an object", source))
        return
    for name in SOVEREIGNTY_REQUIRED_FIELDS:
        if name not in sov:
            findings.append(Finding("BBE-PORT-006", f"sovereignty.{name} missing", source))
    for name in ("weights_portable", "runs_offline"):
        if name in sov and not isinstance(sov[name], bool):
            findings.append(Finding("BBE-PORT-006", f"sovereignty.{name} must be boolean", source))
    region = sov.get("data_region")
    if region is not None and (not isinstance(region, str) or not re.fullmatch(r"[a-z]{2}|eu|self", region)):
        findings.append(
            Finding("BBE-PORT-006", f"sovereignty.data_region invalid: {region!r} (expect ISO-3166 alpha-2 lowercase, 'eu' or 'self')", source)
        )


def _validate_secrets(raw: Dict[str, Any], findings: List[Finding], source: str) -> None:
    ref = raw.get("credential_ref")
    if not isinstance(ref, str) or not CREDENTIAL_REF_RE.match(ref):
        findings.append(
            Finding("BBE-PORT-004", f"credential_ref must be vault://… or env:VAR, got {ref!r}", source)
        )
    for path, value in _walk_strings(raw):
        if path == "credential_ref":
            continue  # already shape-checked above; a valid ref is not a secret
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                findings.append(
                    Finding("BBE-PORT-004", f"field {path} looks like credential material — manifests carry references, never secrets", source)
                )
                break


def validate_manifest(raw: Any, source: str = "") -> List[Finding]:
    """Validate a decoded manifest. Returns findings; empty list means valid."""
    findings: List[Finding] = []

    if not isinstance(raw, dict):
        return [Finding("BBE-PORT-002", "manifest must be a JSON object", source)]

    if raw.get("manifest_version") != MANIFEST_VERSION:
        findings.append(
            Finding("BBE-PORT-001", f"manifest_version must be {MANIFEST_VERSION!r}, got {raw.get('manifest_version')!r}", source)
        )

    for name in MANIFEST_REQUIRED_FIELDS:
        if name not in raw:
            findings.append(Finding("BBE-PORT-002", f"required field missing: {name}", source))

    known = set(MANIFEST_REQUIRED_FIELDS) | set(MANIFEST_OPTIONAL_FIELDS)
    for name in raw:
        if name not in known:
            findings.append(Finding("BBE-PORT-008", f"unknown field: {name}", source))

    ident = raw.get("id")
    match = ID_RE.match(ident) if isinstance(ident, str) else None
    if match is None:
        if "id" in raw:
            findings.append(Finding("BBE-PORT-003", f"id must be '<vendor>/<model>', got {ident!r}", source))
    else:
        vendor, model = match.groups()
        if "vendor" in raw and raw["vendor"] != vendor:
            findings.append(
                Finding("BBE-PORT-003", f"id vendor {vendor!r} contradicts vendor field {raw['vendor']!r}", source)
            )
        if "model" in raw and raw["model"] != model:
            findings.append(
                Finding("BBE-PORT-003", f"id model {model!r} contradicts model field {raw['model']!r}", source)
            )

    for name, allowed in (("role", ROLES), ("deployment", DEPLOYMENTS), ("wire", WIRES)):
        if name in raw and raw[name] not in allowed:
            findings.append(
                Finding("BBE-PORT-006", f"{name} must be one of {', '.join(allowed)}; got {raw[name]!r}", source)
            )

    for name in ("context_tokens", "max_output_tokens"):
        if name in raw:
            value = raw[name]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                findings.append(Finding("BBE-PORT-007", f"{name} must be a positive integer, got {value!r}", source))
    if isinstance(raw.get("context_tokens"), int) and isinstance(raw.get("max_output_tokens"), int):
        if raw["max_output_tokens"] > raw["context_tokens"]:
            findings.append(
                Finding("BBE-PORT-007", "max_output_tokens exceeds context_tokens", source)
            )

    cost = raw.get("cost_per_mtok")
    if cost is not None:
        if not isinstance(cost, dict):
            findings.append(Finding("BBE-PORT-007", "cost_per_mtok must be an object", source))
        else:
            for name in ("input", "output"):
                value = cost.get(name)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                    findings.append(Finding("BBE-PORT-007", f"cost_per_mtok.{name} must be a non-negative number", source))
            if cost.get("currency") not in ("EUR", "USD"):
                findings.append(Finding("BBE-PORT-007", f"cost_per_mtok.currency must be EUR or USD, got {cost.get('currency')!r}", source))

    endpoint_env = raw.get("endpoint_env")
    if endpoint_env is not None and (not isinstance(endpoint_env, str) or not ENDPOINT_ENV_RE.match(endpoint_env)):
        findings.append(
            Finding("BBE-PORT-004", f"endpoint_env must be an env var NAME, got {endpoint_env!r}", source)
        )

    _validate_capabilities(raw, findings, source)
    _validate_sovereignty(raw, findings, source)
    _validate_secrets(raw, findings, source)
    return findings


def load_manifest(path: str | Path) -> Tuple[Manifest | None, List[Finding]]:
    """Load and validate a manifest file. Returns (manifest_or_None, findings)."""
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [Finding("BBE-PORT-002", f"manifest not found: {p}", str(p))]
    except json.JSONDecodeError as exc:
        return None, [Finding("BBE-PORT-002", f"malformed JSON: {exc}", str(p))]

    findings = validate_manifest(raw, source=p.name)
    if findings:
        return None, findings
    return Manifest(raw=raw, source=str(p)), []
