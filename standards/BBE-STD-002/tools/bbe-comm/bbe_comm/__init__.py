"""bbe-comm — BBE Communication Intelligence Tool for BBE-STD-002 v1.0-RC2.

Headless Python package providing block validation, scoring, lineage tracing,
repair suggestions, normalization, incident-pattern detection, AGUARD-decision-
envelope output, and a self-optimization learning loop.

Public API:
    lint(text, filename) -> (blocks, findings)   # backward-compat with RC1 shim
    score(text)          -> list[ScoreResult]
    trace(text, ...)     -> TraceResult
    auth_check(text)     -> AuthCheckResult
    incident_test(text)  -> IncidentResult

CLI: see bbe_comm.cli (entry point: tools/bbe-comm/bbe-comm).
"""

from .constants import PACKAGE_VERSION, PROTOCOL_VERSION
from .validator import lint
from .score import score
from .trace import trace
from .incident import incident_test, auth_check

__version__ = PACKAGE_VERSION

__all__ = [
    "PACKAGE_VERSION",
    "PROTOCOL_VERSION",
    "lint",
    "score",
    "trace",
    "incident_test",
    "auth_check",
]
