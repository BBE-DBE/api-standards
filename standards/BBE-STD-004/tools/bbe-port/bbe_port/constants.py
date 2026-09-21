"""Shared vocabulary for BBE-STD-004 tooling.

Single source of truth for capability flags, enums and finding ids. Keep in
lock-step with ../../schema/*.schema.json.
"""

from __future__ import annotations

MANIFEST_VERSION = "1"
TASK_VERSION = "1"
REPORT_VERSION = "1"

# Capability flags. The first four are REQUIRED in every manifest; the rest
# default to False when absent.
REQUIRED_CAPABILITIES = ("tools", "json_mode", "streaming", "system_prompt")
OPTIONAL_CAPABILITIES = ("vision", "prompt_cache")
ALL_CAPABILITIES = REQUIRED_CAPABILITIES + OPTIONAL_CAPABILITIES

ROLES = ("primary", "fallback", "offline_fallback", "candidate")
DEPLOYMENTS = ("saas", "self_hosted", "on_prem")
WIRES = (
    "anthropic_messages",
    "openai_chat",
    "openai_responses",
    "google_generative",
    "custom",
)

MANIFEST_REQUIRED_FIELDS = (
    "manifest_version",
    "id",
    "vendor",
    "model",
    "role",
    "deployment",
    "wire",
    "credential_ref",
    "context_tokens",
    "max_output_tokens",
    "capabilities",
    "sovereignty",
)
MANIFEST_OPTIONAL_FIELDS = ("endpoint_env", "cost_per_mtok", "notes")

SOVEREIGNTY_REQUIRED_FIELDS = ("data_region", "weights_portable", "runs_offline")

TASK_REQUIRED_FIELDS = ("task_version", "id", "category", "weight", "prompt", "checks")
TASK_OPTIONAL_FIELDS = ("requires", "min_context_tokens", "system", "notes")

CHECK_TYPES = (
    "contains_all",
    "contains_any",
    "not_contains",
    "regex",
    "json_has_keys",
    "equals_normalized",
)

# Findings. Severity is always "error": this tooling sits on a blocking gate,
# so a warning tier would only invite the habit of ignoring it.
FINDINGS = {
    "BBE-PORT-001": "manifest_version missing or unsupported",
    "BBE-PORT-002": "required manifest field missing",
    "BBE-PORT-003": "id does not match '<vendor>/<model>' or contradicts vendor/model fields",
    "BBE-PORT-004": "credential material in manifest (or malformed credential_ref)",
    "BBE-PORT-005": "capability block malformed (unknown key or non-boolean value)",
    "BBE-PORT-006": "enum violation (role / deployment / wire / sovereignty)",
    "BBE-PORT-007": "numeric field invalid (context_tokens / max_output_tokens / cost)",
    "BBE-PORT-008": "unknown top-level manifest field",
    "BBE-TASK-001": "task_version missing or unsupported",
    "BBE-TASK-002": "required task field missing",
    "BBE-TASK-003": "task id malformed",
    "BBE-TASK-004": "check malformed or of unknown type",
    "BBE-TASK-005": "unknown capability in requires[]",
    "BBE-TASK-006": "duplicate task id in corpus",
}

# Defaults
DEFAULT_FLOOR = 0.80
MIN_CORPUS_SIZE_P3 = 20
MAX_EXCERPT_CHARS = 200
