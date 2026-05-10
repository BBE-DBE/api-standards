"""Spec constants for BBE-STD-002 v1.0-RC2.

Single source of truth for the type registry, vocabularies, regexes, and
field-name reservations. Imported by parser, validator, score, and rules.
"""

from __future__ import annotations

import re

# --- Versions --------------------------------------------------------------

PACKAGE_VERSION  = "1.0.0-rc2"   # bbe-comm package version
PROTOCOL_VERSION = "1.0"         # @bbe-comm wire-protocol version
SUPPORTED_PROTOCOL_MAJOR = {1}

# --- Type registry (RC2 §5.4) ----------------------------------------------

REGISTERED_TYPES = {
    "operator_prompt",
    "operator_auth",
    "operator_deny",
    "operator_context",
    "operator_query",
    "agent_result",
    "agent_progress",
    "agent_query",
    "agent_warning",
    "agent_abort",
    "guard_decision",
    "audit_record",
}

# Types that act as roots (need no @parent_id at L4)
ROOT_TYPES = {"operator_prompt"}

# Type-slug prefix per @type — for BBE-COMM-012 (slug-mismatch warning)
TYPE_TO_SLUG = {
    "operator_prompt":  "op_prompt",
    "operator_auth":    "op_auth",
    "operator_deny":    "op_deny",
    "operator_context": "op_ctx",
    "operator_query":   "op_query",
    "agent_result":     "agent_result",
    "agent_progress":   "agent_progress",
    "agent_query":      "agent_query",
    "agent_warning":    "agent_warn",
    "agent_abort":      "agent_abort",
    "guard_decision":   "guard_dec",
    "audit_record":     "audit",
}

# Type-restricted @status values — RC2 §5.5
REGISTERED_STATUSES_BY_TYPE = {
    "agent_result":   {"complete", "partial", "blocked", "failed"},
    "agent_progress": {"starting", "running", "paused"},
    "operator_auth":  {"active", "expired", "revoked", "consumed"},
}

# --- Reserved field-names (RC2 §5.1, §5.2) ---------------------------------

COMMON_RESERVED_FIELDS = {
    "bbe-comm",
    "type",
    "id",
    "parent_id",
    "correlation_id",
    "refs",
    "agent",
    "timestamp",
    "host",
    "status",
    "compliance_level",
    # L5 marker fields (RC2 §8) — opaque values, shape-checked only in v1.0
    "x-bbe-sig",
    "x-bbe-ledger",
    "x-bbe-attest",
}

# Auth-only fields (allowed only on operator_auth or operator_deny per check_022)
# For check_017 (extension prefix), these are also "reserved-but-conditional".
AUTH_ONLY_FIELDS = {
    "scope":      {"operator_auth"},
    "target":     {"operator_auth"},
    "ttl":        {"operator_auth"},
    "issued_by":  {"operator_auth"},
    "not_after":  {"operator_auth"},
    "scope_mode": {"operator_auth"},  # RC2: multi-scope semantic
    "nonce":      {"operator_auth", "operator_deny"},
    "hmac":       {"operator_auth", "operator_deny"},
    "revokes":    {"operator_deny"},
    "reason":     {"operator_deny", "agent_abort", "guard_decision"},
    "ask":        {"operator_query", "agent_query"},
    "severity":   {"agent_warning"},
    "layer":      {"guard_decision"},
    "tool":       {"guard_decision"},
    "decision":   {"guard_decision"},
    "subject":    {"audit_record"},
    "action":     {"audit_record"},
    "actor":      {"audit_record"},
    "outcome":    {"audit_record"},
}

TYPE_SPECIFIC_FIELDS = set(AUTH_ONLY_FIELDS.keys())

ALL_RESERVED_FIELDS = COMMON_RESERVED_FIELDS | TYPE_SPECIFIC_FIELDS

# Anti-inference forbidden field-names (BBE-COMM-016) — outside operator_auth
FORBIDDEN_AUTH_INFERENCE_FIELDS = {
    "authorize",
    "authorized",
    "authorization",
    "authority",
}

# --- Scope vocabulary (RC2 §7.3) -------------------------------------------

CANONICAL_SCOPES = {
    "pm2-mutate",
    "git-push",
    "git-remote-change",
    "systemctl-mutate",
    "docker-mutate",
    "gh-mutate",
    "http-mutate",
    "db-mutate",
    "fs-mutate-system",
    "secret-rotate",
}

SCOPE_MODE_VALUES = {"all", "any"}

# TTL policy maximum (RC2 §5.2 / BBE-COMM-025)
TTL_MAX_SECONDS = 3600

# --- Regexes ---------------------------------------------------------------

OPEN_TAG_RE  = re.compile(r"^\[([A-Z][A-Z0-9_-]*)\]\s*$")
CLOSE_TAG_RE = re.compile(r"^\[/([A-Z][A-Z0-9_-]*)\]\s*$")
HEADER_RE    = re.compile(r"^@([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
LABEL_RE     = re.compile(r"^[A-Z][A-Z0-9_-]*$")

CANONICAL_ID_RE = re.compile(
    r"^[a-z][a-z0-9_]{1,16}_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z_[a-f0-9]{8}$"
)
INTEROP_ID_RE = re.compile(r"^[a-z]{3,16}_[A-Za-z0-9_-]{8,64}$")

PROTOCOL_VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")
EXTENSION_FIELD_RE  = re.compile(r"^x-[a-z][a-z0-9-]{1,31}-[a-zA-Z][a-zA-Z0-9_-]*$")
EXTENSION_TYPE_RE   = re.compile(r"^x-[a-z][a-z0-9-]{1,31}-[a-zA-Z][a-zA-Z0-9_-]*$")
COMPLIANCE_LEVEL_RE = re.compile(r"^L[0-5]$")
TTL_RE              = re.compile(r"^([1-9][0-9]*)([smh])$")
HMAC_RE             = re.compile(r"^sha256:[a-f0-9]{64}$")
NONCE_RE            = re.compile(r"^[a-f0-9]{4,16}$")
AGENT_FIELD_RE      = re.compile(r"^[a-z0-9][a-z0-9._-]*@[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+$")

# L5 marker shapes (opaque values in v1.0; STD-003 will tighten)
L5_SIG_SHAPE_RE     = re.compile(r"^[A-Za-z0-9+/=._:-]{16,}$")
L5_LEDGER_SHAPE_RE  = re.compile(r"^[A-Za-z0-9+/=._:-]{8,}$")
L5_ATTEST_SHAPE_RE  = re.compile(r"^[A-Za-z0-9+/=._:-]{8,}$")

# --- Phrase-set for incident detection (RC2 §17.1) -------------------------
# Used by incident.py to detect prose-only auth-inference attempts.
INCIDENT_PROSE_PATTERNS = [
    r"\byes\s+please\s+go\s+ahead\b",
    r"\bplease\s+proceed\b",
    r"\byou\s+are\s+authoriz",
    r"\bgo\s+ahead\b",
    r"\bproceed\s+with\b",
    r"\bconfirm(ed)?\s+(go|deploy|push|merge)",
    r"\b(GO|GO!|GO\s+GO)\b",
    r"\bauthoriz(ed|ation)\s+to\s+(deploy|push|merge|reload)",
]

# Whether incident-test exit-codes-4 on detected pattern even when the prose
# is in an OPERATOR-CONTEXT (informational) block. Default: yes — a context
# block that LOOKS like authorization is still a regression risk.
INCIDENT_FIRES_ON_CONTEXT = True
