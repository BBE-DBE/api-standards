"""Compliance-level scoring (RC2 §8).

RC2 CORRECTION vs RC1:
  L4 = lineage-complete + HMAC-anchored (when type ∈ {operator_auth, operator_deny})
  L5 = + at least one of @x-bbe-sig / @x-bbe-ledger / @x-bbe-attest (shape-valid)

HMAC alone is NOT L5. L5 is reserved for externally-auditable
(asymmetric-signature, hash-linked-ledger, attestation-witnessed) anchors.
The mechanism for L5 is owned by STD-003; this scorer only checks shape.
"""

from __future__ import annotations

from .constants import (
    HMAC_RE, ROOT_TYPES,
    L5_SIG_SHAPE_RE, L5_LEDGER_SHAPE_RE, L5_ATTEST_SHAPE_RE,
)
from .model import Block, ScoreResult


def compute_level(b: Block) -> int:
    """Compute L0..L5 from features present on the block.

    L1 — block parsed (always true if we have a Block)
    L2 — + @bbe-comm and @type
    L3 — + @id (any acceptable form)
    L4 — + lineage-integrity (root type OR @parent_id present)
       — and, for operator_auth/operator_deny, valid-shape @hmac
    L5 — + at least one valid-shape L5 marker field
    """
    h = b.headers
    if not h.get("bbe-comm") or not h.get("type"):
        return 1
    if not h.get("id"):
        return 2
    type_v = h.get("type", "")
    is_root = type_v in ROOT_TYPES
    if not is_root and not h.get("parent_id"):
        return 3

    # L4 floor reached. For auth blocks, HMAC must be present and shape-valid.
    if type_v in {"operator_auth", "operator_deny"}:
        if not HMAC_RE.match(h.get("hmac", "") or ""):
            return 3  # missing HMAC drops back to L3
    # else: non-auth block reached L4 simply by lineage.

    # L5: at least one external-audit anchor (shape-valid)
    sig    = h.get("x-bbe-sig", "")
    ledger = h.get("x-bbe-ledger", "")
    attest = h.get("x-bbe-attest", "")
    if (sig and L5_SIG_SHAPE_RE.match(sig)) \
            or (ledger and L5_LEDGER_SHAPE_RE.match(ledger)) \
            or (attest and L5_ATTEST_SHAPE_RE.match(attest)):
        return 5

    return 4


def _level_rationale(b: Block, computed: int) -> str:
    h = b.headers
    parts: list[str] = []
    if h.get("bbe-comm"):
        parts.append("@bbe-comm")
    if h.get("type"):
        parts.append("@type")
    if h.get("id"):
        parts.append("@id")
    type_v = h.get("type", "")
    if type_v in ROOT_TYPES:
        parts.append("(root type — no @parent_id needed)")
    elif h.get("parent_id"):
        parts.append("@parent_id")
    if type_v in {"operator_auth", "operator_deny"} and HMAC_RE.match(h.get("hmac", "") or ""):
        parts.append("@hmac (valid shape)")
    if computed == 5:
        if h.get("x-bbe-sig"):    parts.append("@x-bbe-sig")
        if h.get("x-bbe-ledger"): parts.append("@x-bbe-ledger")
        if h.get("x-bbe-attest"): parts.append("@x-bbe-attest")
    return f"L{computed} from features: {', '.join(parts) if parts else '(none)'}"


def score_block(b: Block) -> ScoreResult:
    h = b.headers
    declared_raw = h.get("compliance_level")
    declared: int | None = None
    if declared_raw and len(declared_raw) == 2 and declared_raw.startswith("L"):
        try:
            declared = int(declared_raw[1])
        except ValueError:
            declared = None
    computed = compute_level(b)
    return ScoreResult(
        block_label=b.label,
        block_id=h.get("id"),
        block_type=h.get("type"),
        declared_level=declared,
        computed_level=computed,
        over_claim=(declared is not None and declared > computed),
        rationale=_level_rationale(b, computed),
    )


def score(text: str) -> list[ScoreResult]:
    """Convenience: parse + score-each-block."""
    from .parser import parse_blocks  # local import avoids cycle at module-load
    blocks, _ = parse_blocks(text)
    return [score_block(b) for b in blocks]
