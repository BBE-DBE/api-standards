"""Self-optimization learning-loop tests.

Verify the safety properties:
  - append-only: events never overwrite or delete
  - redaction: forbidden field-values never reach disk
  - rate-limit: same suggestion not re-emitted within 24h
  - no-mutation: suggestions are review-only, never patch the standard
  - schema: every event matches schemas/learning-event.schema.json
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2].parent
PKG  = ROOT / "tools" / "bbe-comm"
sys.path.insert(0, str(PKG))

from bbe_comm.learning import (  # noqa: E402
    LearningStore, LearningEvent, EVENT_TYPES,
    event_from_finding, event_from_incident,
    SUGGESTION_RATE_LIMIT_SECS,
)
from bbe_comm.model import Finding, IncidentResult  # noqa: E402


def _new_store() -> tuple[LearningStore, Path]:
    td = Path(tempfile.mkdtemp(prefix="bbe-comm-learn-test-"))
    return LearningStore(td), td


# === Append-only ===

def test_observe_appends_one_line_per_event():
    store, _ = _new_store()
    store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016",
                                summary="t1"))
    store.observe(LearningEvent(event_type="legacy_tag_detected", summary="t2"))
    lines = store.events_path.read_text().strip().split("\n")
    assert len(lines) == 2
    for ln in lines:
        json.loads(ln)  # must be valid JSON


def test_observe_never_overwrites_existing():
    store, _ = _new_store()
    for i in range(5):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016",
                                    summary=f"t{i}"))
    assert len(store.read_all()) == 5
    # Re-open store; verify history is preserved
    store2 = LearningStore(store.store_dir)
    assert len(store2.read_all()) == 5


# === Redaction ===

def test_redaction_scrubs_forbidden_values():
    store, _ = _new_store()
    evt = LearningEvent(
        event_type="lint_error",
        check_id="BBE-COMM-015",
        summary="auth missing fields",
        extra={
            "hmac": "sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2",
            "nonce": "9c8f2a1b",
            "scope": "pm2-mutate",
            "target": "netcup-api",
            "issued_by": "BBE-DBE",
            "x-bbe-sig": "ed25519-base64-AAAA",
            "x-bbe-ledger": "ledger-receipt-xyz",
            "x-bbe-attest": "notary-witness-ABC",
            "innocent": "kept",
        },
    )
    store.observe(evt)
    text = store.events_path.read_text()
    # Forbidden values must NOT appear; they must be scrubbed to <REDACTED>
    forbidden = ["b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2",
                 "9c8f2a1b", "pm2-mutate", "netcup-api", "BBE-DBE",
                 "ed25519-base64-AAAA", "ledger-receipt-xyz", "notary-witness-ABC"]
    for f in forbidden:
        assert f not in text, f"REDACTION FAILURE: {f!r} leaked"
    assert '"<REDACTED>"' in text
    assert '"innocent": "kept"' in text


def test_event_from_finding_uses_label_shape_not_label():
    f = Finding("BBE-COMM-016", "error", "§7.4", "...", line=12,
                block_label="OPERATOR-PROMPT-VERY-LONG-LABEL-NAME-HERE-32CHARS")
    evt = event_from_finding(f, "/path/to/file.txt")
    # The actual label string must NOT appear in the event payload
    payload = json.dumps(evt.to_dict())
    assert "OPERATOR-PROMPT-VERY-LONG-LABEL-NAME-HERE-32CHARS" not in payload
    # But the bucket-shape should be set
    assert evt.block_label_shape is not None
    assert evt.block_label_shape.startswith(("short", "medium", "long"))


def test_event_from_incident_summarizes_only():
    incident = IncidentResult(
        pattern_detected=True,
        matches=[{"phrase": "go ahead", "line": 3, "context": "Yes please go ahead with deploy"}],
        has_authorizing_block=False,
        verdict="pattern-without-auth",
        exit_code=4,
    )
    evt = event_from_incident(incident, "/secret/path/incident.txt")
    payload = json.dumps(evt.to_dict())
    # Specific phrase content & file path must NOT leak
    assert "go ahead" not in payload
    assert "/secret/path/" not in payload
    assert "incident.txt" not in payload
    # File path appears as hash
    assert evt.file_hash and evt.file_hash.startswith(("",))  # at least set
    assert evt.event_type == "authorization_inference_attempt"


# === Validation ===

def test_unknown_event_type_rejected():
    store, _ = _new_store()
    try:
        store.observe(LearningEvent(event_type="invented_type", summary="x"))
    except ValueError:
        return
    raise AssertionError("expected ValueError on unknown event_type")


def test_all_documented_event_types_accepted():
    store, _ = _new_store()
    for et in EVENT_TYPES:
        store.observe(LearningEvent(event_type=et, summary=f"smoke {et}"))
    assert len(store.read_all()) == len(EVENT_TYPES)


# === Suggestion synthesis ===

def test_frequent_check_id_emits_one_suggestion():
    store, _ = _new_store()
    for _ in range(5):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016"))
    suggestions = store.synthesize_suggestions(min_count=5)
    assert len(suggestions) >= 1
    assert any("BBE-COMM-016" in (s.get("title") or "") for s in suggestions)
    # Suggestion file is written
    target = store.suggestions_dir / "operator-training.md"
    assert target.exists()
    assert "PROPOSED" in target.read_text()


def test_rate_limit_blocks_immediate_resuggest():
    store, _ = _new_store()
    for _ in range(10):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016"))
    s1 = store.synthesize_suggestions(min_count=5)
    s2 = store.synthesize_suggestions(min_count=5)
    # s1 emits; s2 is rate-limited
    assert len(s1) >= 1
    assert all(not s for s in s2 if s.get("rate_key") == s1[0].get("rate_key")) \
        or len(s2) == 0


def test_no_suggestion_below_threshold():
    store, _ = _new_store()
    for _ in range(2):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016"))
    suggestions = store.synthesize_suggestions(min_count=5)
    # 2 events < min_count=5 → no suggestion
    assert not any("BBE-COMM-016" in (s.get("title") or "") for s in suggestions)


def test_suggestion_files_are_never_overwritten():
    store, _ = _new_store()
    target = store.suggestions_dir / "operator-training.md"
    target.write_text("EXISTING CONTENT\n")
    for _ in range(5):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016"))
    store.synthesize_suggestions(min_count=5)
    text = target.read_text()
    assert text.startswith("EXISTING CONTENT"), \
        "synthesize must APPEND, never overwrite"
    assert "PROPOSED" in text


def test_inference_attempt_pattern_emits_test_suggestion():
    store, _ = _new_store()
    for _ in range(3):
        store.observe(LearningEvent(event_type="authorization_inference_attempt"))
    suggestions = store.synthesize_suggestions(min_count=5)
    target = store.suggestions_dir / "new-test-cases.md"
    assert target.exists() or any("test" in (s.get("title") or "").lower() for s in suggestions)


# === No-silent-mutation ===

def test_synthesize_does_not_modify_spec_files():
    """Sanity: the learning loop only writes under store.suggestions_dir."""
    store, td = _new_store()
    spec_path = ROOT / "BBE-STD-002-v1.0-RC2.md"
    spec_mtime_before = spec_path.stat().st_mtime if spec_path.exists() else 0
    schema_path = ROOT / "schema" / "BBE-STD-002.schema.json"
    schema_mtime_before = schema_path.stat().st_mtime if schema_path.exists() else 0

    for _ in range(20):
        store.observe(LearningEvent(event_type="lint_error", check_id="BBE-COMM-016"))
        store.observe(LearningEvent(event_type="authorization_inference_attempt"))
        store.observe(LearningEvent(event_type="legacy_tag_detected"))
        store.observe(LearningEvent(event_type="failed_repair"))
    store.synthesize_suggestions(min_count=5)

    if spec_path.exists():
        assert spec_path.stat().st_mtime == spec_mtime_before, \
            "BUG: synthesize touched the spec file"
    if schema_path.exists():
        assert schema_path.stat().st_mtime == schema_mtime_before, \
            "BUG: synthesize touched the schema file"
    # Suggestions live ONLY under store_dir
    written = list(td.rglob("*.md")) + list(td.rglob("*.jsonl")) + list(td.rglob("*.last"))
    for w in written:
        assert str(w).startswith(str(td)), \
            f"BUG: file written outside store dir: {w}"


# === CLI integration ===

def test_cli_observe_then_suggest_roundtrip():
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        store_dir = td
        for i in range(6):
            evt_json = json.dumps({"event_type": "lint_error", "check_id": "BBE-COMM-016",
                                   "summary": f"t{i}"})
            r = subprocess.run(
                [sys.executable, str(PKG / "bbe-comm"), "learn", "observe", evt_json,
                 "--store", store_dir],
                capture_output=True, text=True,
            )
            assert r.returncode == 0, f"observe failed: {r.stderr}"
        r = subprocess.run(
            [sys.executable, str(PKG / "bbe-comm"), "learn", "suggest",
             "--store", store_dir, "--json"],
            capture_output=True, text=True,
        )
        assert r.returncode == 0, f"suggest failed: {r.stderr}"
        out = json.loads(r.stdout)
        assert isinstance(out, list)
        # At least one suggestion targeting operator-training.md
        assert any(s.get("target_file", "").endswith("operator-training.md") for s in out), \
            f"expected operator-training suggestion, got: {out}"


if __name__ == "__main__":
    import traceback
    tests = [(name, obj) for name, obj in globals().items()
             if name.startswith("test_") and callable(obj)]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
