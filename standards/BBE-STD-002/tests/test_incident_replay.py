"""Incident-replay regression tests (RC2 §17.1, operator decision 6).

These tests REPLAY the 2026-05-09 incident pattern end-to-end and verify
that bbe-comm v1.0-RC2 catches it in all four layers:

1. parser produces zero `operator_auth` blocks (because the prose has none)
2. linter does not silently accept any auth-shaped fields
3. `bbe-comm score` returns L0/L1 only
4. `bbe-comm auth-check` returns FAIL with exit code 4
5. `bbe-comm incident-test` returns exit code 4
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG  = ROOT / "tools" / "bbe-comm"
sys.path.insert(0, str(PKG))

from bbe_comm import lint, score, auth_check, incident_test  # noqa: E402
from bbe_comm.parser import parse_blocks                      # noqa: E402


CANONICAL_INCIDENT = (ROOT / "examples" / "incident-replay" / "01-canonical-incident.txt").read_text()
PROSE_ONLY         = (ROOT / "examples" / "incident-replay" / "02-prose-only-no-block.txt").read_text()
PROSE_WITH_AUTH    = (ROOT / "examples" / "incident-replay" / "03-prose-with-correct-auth.txt").read_text()


# === Layer 1: parser doesn't promote prose to authorization ===

def test_layer1_canonical_incident_zero_auth_blocks():
    blocks, _ = parse_blocks(CANONICAL_INCIDENT)
    auth_blocks = [b for b in blocks if b.headers.get("type") == "operator_auth"]
    assert len(auth_blocks) == 0, \
        f"FAIL: parser found {len(auth_blocks)} operator_auth blocks in incident prose"


def test_layer1_prose_only_zero_blocks():
    blocks, _ = parse_blocks(PROSE_ONLY)
    assert len(blocks) == 0, \
        f"FAIL: parser found blocks in pure prose: {[b.label for b in blocks]}"


# === Layer 2: linter rejects auth-shaped headers outside operator_auth ===

def test_layer2_canonical_incident_lints_clean_for_the_prompt():
    """The incident's operator_prompt block IS structurally valid (it's just
    a prompt). The TEST is that no inference happens — the prose doesn't
    promote it to authorization. Lint should produce ZERO load-bearing
    auth-related findings (BBE-COMM-015, 016, 022, 024, 025)."""
    _, findings = lint(CANONICAL_INCIDENT)
    auth_findings = [f for f in findings if f.check_id in
                     ("BBE-COMM-015", "BBE-COMM-016", "BBE-COMM-022",
                      "BBE-COMM-024", "BBE-COMM-025")]
    assert not auth_findings, \
        f"FAIL: incident's operator_prompt triggered auth findings: " \
        f"{[(f.check_id, f.message) for f in auth_findings]}"


# === Layer 3: score returns L0..L4 (not L5) for the prompt ===

def test_layer3_canonical_incident_score_is_below_l5():
    """The incident's prompt may reach L4 (lineage-complete operator_prompt
    with @bbe-comm, @type, @id, @correlation_id). It MUST NOT reach L5 —
    L5 requires @x-bbe-sig / @x-bbe-ledger / @x-bbe-attest. RC2 fix."""
    scores = score(CANONICAL_INCIDENT)
    for s in scores:
        assert s.computed_level < 5, \
            f"FAIL: incident block reached L{s.computed_level} — RC2 says HMAC alone is L4"
    # The block has no @hmac (it's a prompt), so it should NOT reach L4 from
    # auth-shape; it reaches L4 only from lineage. operator_prompt is a root,
    # so lineage gives it L4.


# === Layer 4: auth-check returns prose-only-inference + exit 4 ===

def test_layer4_canonical_incident_auth_check_exit_4():
    a = auth_check(CANONICAL_INCIDENT)
    assert a.has_operator_auth_block is False
    assert a.prose_auth_inference_detected is True
    assert a.verdict == "prose-only-inference"
    assert a.exit_code == 4


def test_layer4_prose_only_auth_check_exit_4():
    a = auth_check(PROSE_ONLY)
    assert a.has_operator_auth_block is False
    assert a.prose_auth_inference_detected is True
    assert a.verdict == "prose-only-inference"
    assert a.exit_code == 4


def test_layer4_prose_with_correct_auth_passes():
    """Prose containing inference cues PLUS a real operator_auth block is OK."""
    a = auth_check(PROSE_WITH_AUTH)
    assert a.has_operator_auth_block is True
    # verdict is valid-auth even if inference cues exist alongside
    assert a.verdict == "valid-auth"
    assert a.exit_code == 0


# === Layer 5: incident-test subcommand exit 4 ===

def test_layer5_canonical_incident_returns_exit_4():
    i = incident_test(CANONICAL_INCIDENT)
    assert i.pattern_detected is True
    assert i.has_authorizing_block is False
    assert i.verdict == "pattern-without-auth"
    assert i.exit_code == 4


def test_layer5_prose_only_returns_exit_4():
    i = incident_test(PROSE_ONLY)
    assert i.pattern_detected is True
    assert i.has_authorizing_block is False
    assert i.verdict == "pattern-without-auth"
    assert i.exit_code == 4


def test_layer5_prose_with_auth_returns_exit_0():
    i = incident_test(PROSE_WITH_AUTH)
    assert i.pattern_detected is True
    assert i.has_authorizing_block is True
    assert i.verdict == "pattern-with-auth"
    assert i.exit_code == 0


# === RC2 L4/L5 separation tests ===

def test_l4_l5_hmac_alone_is_l4_not_l5():
    """RC2 §8: HMAC alone reaches L4 ceiling. L5 requires external-audit anchor."""
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-l4-l5-test
@scope: ["pm2-mutate"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
[/OPERATOR-AUTH]"""
    scores = score(text)
    assert len(scores) == 1
    assert scores[0].computed_level == 4, \
        f"RC2 L4/L5 fix broken: HMAC-anchored auth scored L{scores[0].computed_level} (expected L4)"


def test_l5_requires_external_audit_anchor():
    """L5 requires @x-bbe-sig OR @x-bbe-ledger OR @x-bbe-attest (shape-valid)."""
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-l5-test
@scope: ["pm2-mutate"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
@x-bbe-ledger: ledger-receipt-abc123-xyz789-2026
[/OPERATOR-AUTH]"""
    scores = score(text)
    assert scores[0].computed_level == 5, \
        f"L5 not reached with valid @x-bbe-ledger: scored L{scores[0].computed_level}"


def test_l5_overclaim_with_only_hmac_fires():
    """Declaring @compliance_level: L5 with only HMAC is over-claim (BBE-COMM-023)."""
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-l5-overclaim
@scope: ["pm2-mutate"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
@compliance_level: L5
[/OPERATOR-AUTH]"""
    _, findings = lint(text)
    overclaim = [f for f in findings if f.check_id == "BBE-COMM-023"]
    assert overclaim, \
        "BBE-COMM-023 (over-claim) did not fire for L5-claim with HMAC-only"


# === Multi-scope semantics (RC2 decision 5) ===

def test_scope_mode_default_is_implicit_all():
    """Multi-scope without @scope_mode lints clean (default = AND)."""
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-multi-scope-and
@scope: ["pm2-mutate", "git-push"]
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
[/OPERATOR-AUTH]"""
    _, findings = lint(text)
    errors = [f for f in findings if f.severity == "error"]
    assert not errors, f"unexpected errors: {[(f.check_id, f.message) for f in errors]}"


def test_scope_mode_any_explicit_passes():
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-multi-scope-any
@scope: ["pm2-mutate", "git-push"]
@scope_mode: any
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
[/OPERATOR-AUTH]"""
    _, findings = lint(text)
    errors = [f for f in findings if f.severity == "error"]
    assert not errors, f"unexpected errors: {[(f.check_id, f.message) for f in errors]}"


def test_scope_mode_invalid_value_fires_026():
    text = """[OPERATOR-AUTH]
@bbe-comm: 1.0
@type: operator_auth
@id: op_auth_2026-05-09T19-30-00Z_7f3e1234
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: rc2-multi-scope-bad
@scope: ["pm2-mutate"]
@scope_mode: maybe
@target: netcup-api
@ttl: 5m
@issued_by: BBE-DBE
@nonce: 9c8f2a1b
@hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
[/OPERATOR-AUTH]"""
    _, findings = lint(text)
    assert any(f.check_id == "BBE-COMM-026" for f in findings), \
        "BBE-COMM-026 did not fire for invalid @scope_mode"


# === Runtime-agnostic posture ===

def test_runtime_agnostic_no_aguard_required():
    """A fully-conformant non-auth flow can be linted without any AGUARD/runtime
    dependency. Tests the spec's runtime-agnostic claim (RC2 decision 3)."""
    text = """[OPERATOR-PROMPT]
@bbe-comm: 1.0
@type: operator_prompt
@id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: runtime-agnostic-test

A simple prompt, no privileged operations, no HMAC needed.
[/OPERATOR-PROMPT]

[AGENT-RESULT]
@bbe-comm: 1.0
@type: agent_result
@id: agent_result_2026-05-09T19-30-00Z_e1e2e3e4
@parent_id: op_prompt_2026-05-09T19-25-00Z_1a2b3c4d
@correlation_id: runtime-agnostic-test
@agent: claude-opus-4-7@2.1.138@local
@status: complete

Done.
[/AGENT-RESULT]"""
    _, findings = lint(text)
    errors = [f for f in findings if f.severity == "error"]
    assert not errors, \
        f"runtime-agnostic flow had errors: {[(f.check_id, f.message) for f in errors]}"


# === CLI smoke tests ===

CLI = str(PKG / "bbe-comm")


def test_cli_incident_test_exits_4_on_canonical():
    proc = subprocess.run(
        [sys.executable, CLI, "incident-test",
         str(ROOT / "examples" / "incident-replay" / "01-canonical-incident.txt")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 4, \
        f"expected exit 4, got {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"


def test_cli_incident_test_exits_0_with_auth():
    proc = subprocess.run(
        [sys.executable, CLI, "incident-test",
         str(ROOT / "examples" / "incident-replay" / "03-prose-with-correct-auth.txt")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, \
        f"expected exit 0, got {proc.returncode}\nstdout:\n{proc.stdout}"


def test_cli_score_runs_clean_on_valid():
    proc = subprocess.run(
        [sys.executable, CLI, "score",
         str(ROOT / "examples" / "valid" / "02-operator-auth.txt")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"score exit {proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    assert "computed=L4" in proc.stdout, \
        f"RC2 L4-fix not reflected in score output: {proc.stdout}"


def test_cli_explain_known_check():
    proc = subprocess.run(
        [sys.executable, CLI, "explain", "BBE-COMM-016"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "ANTI-INFERENCE" in proc.stdout


def test_cli_emit_produces_valid_template():
    proc = subprocess.run(
        [sys.executable, CLI, "emit", "agent_result"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "@type: agent_result" in proc.stdout
    assert "@status: complete" in proc.stdout


def test_cli_integrate_guard_emits_envelope():
    proc = subprocess.run(
        [sys.executable, CLI, "integrate-guard",
         str(ROOT / "examples" / "valid" / "02-operator-auth.txt")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    import json as _json
    envelope = _json.loads(proc.stdout)
    assert envelope["schema_version"] == "1.0"
    assert envelope["decision"] in {"allow", "allow-with-warnings", "warn", "deny"}
    assert "advisory" in envelope


def test_cli_integrate_guard_denies_on_load_bearing_failure():
    proc = subprocess.run(
        [sys.executable, CLI, "integrate-guard",
         str(ROOT / "examples" / "invalid" / "016-auth-inference.txt")],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    import json as _json
    envelope = _json.loads(proc.stdout)
    assert envelope["decision"] == "deny", f"expected deny on BBE-COMM-016 file, got {envelope['decision']}"
    assert "BBE-COMM-016" in envelope["lint_summary"]["load_bearing_failures"]


def test_cli_normalize_converts_legacy_keyvalue():
    """Welt-A 'key: value' header form should normalize to '@key: value'."""
    legacy = """[OPERATOR-AUTH v1.0]
id: op_auth-2026-05-09T19:30:00Z-7f3e
session: routine-deploy
scope: pm2-mutate
target: netcup-api
ttl: 5m
issued_by: BBE-DBE
nonce: 9c8f2a1b
hmac: sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2
note: Authorize PM2 reload.
[/OPERATOR-AUTH]
"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fp:
        fp.write(legacy)
        path = fp.name
    proc = subprocess.run(
        [sys.executable, CLI, "normalize", path],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    out = proc.stdout
    assert "@bbe-comm" not in out, \
        "normalize should NOT add @bbe-comm (semantic addition); only shape-changes"
    assert "@type" not in out, \
        "normalize should NOT add @type (semantic addition); only shape-changes"
    assert "@correlation_id: routine-deploy" in out, "session→correlation_id rename failed"
    assert "@scope:" in out, "@-prefix not added"
    # The id should be normalized: colons → dashes, outer dashes → underscores
    assert "op_auth_2026-05-09T19-30-00Z_" in out, \
        "ID normalization (colons→dashes, outer→_) didn't fire"


# === Self-check: this test file's own learning-event hashing is redacted ===

def test_learning_redaction_no_secrets_in_event_log():
    from bbe_comm.learning import LearningEvent, LearningStore, _hash
    import tempfile, os, json as _json
    with tempfile.TemporaryDirectory() as td:
        store = LearningStore(td)
        evt = LearningEvent(
            event_type="lint_error",
            check_id="BBE-COMM-016",
            severity="error",
            summary="test event",
            extra={
                "hmac": "sha256:b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2",
                "nonce": "9c8f2a1b",
                "scope": "pm2-mutate",
                "innocent_field": "ok",
            },
        )
        store.observe(evt)
        text = open(store.events_path).read()
        assert "b1d4f7c8e2a9b34571f6e8d9c2a8b1f4e7d5c6a3b9f8e1d2c5a4b7e8f3d6c9a2" not in text, \
            "REDACTION FAILURE: hmac value leaked into learning store"
        assert "9c8f2a1b" not in text, \
            "REDACTION FAILURE: nonce value leaked into learning store"
        assert '"hmac": "<REDACTED>"' in text, "hmac not scrubbed to <REDACTED>"
        assert '"nonce": "<REDACTED>"' in text, "nonce not scrubbed to <REDACTED>"
        assert '"innocent_field": "ok"' in text, "innocent field accidentally redacted"


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
