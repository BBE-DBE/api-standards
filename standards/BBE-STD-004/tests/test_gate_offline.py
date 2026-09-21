"""Gate semantics, swap check and CLI exit codes — fully offline.

Every assertion here runs against the mock transport. A portability gate that
needs credentials to be tested is a gate nobody runs.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _harness import EXAMPLES, TOOL_ROOT, eq, ok, run_suite

from bbe_port.manifest import load_manifest
from bbe_port.runner import block_reason, run_corpus, verdict_for
from bbe_port.swap import compare
from bbe_port.tasks import load_corpus
from bbe_port.transports import TransportError
from bbe_port.transports.mock import MockTransport

FIXTURE = EXAMPLES / "fixtures" / "demo-responses.json"
CLI = TOOL_ROOT / "bbe-port"

PRIMARY = EXAMPLES / "manifests" / "primary-saas.json"
FALLBACK = EXAMPLES / "manifests" / "fallback-saas.json"
OFFLINE = EXAMPLES / "manifests" / "offline-selfhosted.json"


def _load(path):
    manifest, findings = load_manifest(path)
    eq(findings, [], f"{Path(path).name} valid")
    return manifest


def _run(manifest_path, floor=0.80):
    tasks, findings = load_corpus(EXAMPLES / "tasks")
    eq(findings, [], "corpus clean")
    return run_corpus(tasks, _load(manifest_path), MockTransport(FIXTURE), floor)


def _cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=str(TOOL_ROOT)
    )


# --- blocking semantics ----------------------------------------------------

def test_block_reason_names_missing_capability():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    by_id = {t.id: t for t in tasks}
    offline = _load(OFFLINE)
    ok("tools" in block_reason(by_id["call-ip-reservation-tool"], offline), "tool gap named")
    eq(block_reason(by_id["classify-support-ticket"], offline), "", "unconstrained task is runnable")


def test_block_reason_catches_context_shortfall():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    by_id = {t.id: t for t in tasks}
    reason = block_reason(by_id["long-contract-clause-lookup"], _load(OFFLINE))
    ok("context" in reason and "32768" in reason, f"context gap named: {reason!r}")
    eq(block_reason(by_id["long-contract-clause-lookup"], _load(PRIMARY)), "", "200k context is enough")


def test_blocked_tasks_leave_the_denominator():
    """A provider must not score better by being less capable."""
    report = _run(OFFLINE)
    totals = report["totals"]
    eq(totals["blocked"], 2, "blocked count")
    eq(totals["blocked_weight"], 5, "blocked weight")
    eq(totals["scored_weight"], 15, "scored weight excludes blocked")
    eq(totals["scored_weight"] + totals["blocked_weight"], 20, "weights account for the whole corpus")


# --- scoring and verdicts --------------------------------------------------

def test_primary_scores_clean():
    report = _run(PRIMARY)
    eq(report["score"], 1.0, "score")
    eq(report["verdict"], "QUALIFIED", "verdict")
    eq(report["totals"]["blocked"], 0, "nothing blocked")


def test_offline_is_degraded_not_disqualified():
    report = _run(OFFLINE)
    eq(report["score"], 0.8, "12 of 15 scored weight")
    eq(report["verdict"], "QUALIFIED_DEGRADED", "blocked>0 downgrades the verdict but does not fail it")


def test_floor_is_inclusive_and_decisive():
    eq(_run(OFFLINE, floor=0.80)["verdict"], "QUALIFIED_DEGRADED", "score == floor qualifies")
    eq(_run(OFFLINE, floor=0.85)["verdict"], "NOT_QUALIFIED", "raising the floor disqualifies")


def test_verdict_table():
    eq(verdict_for(0.9, 0.8, 0), "QUALIFIED")
    eq(verdict_for(0.9, 0.8, 3), "QUALIFIED_DEGRADED")
    eq(verdict_for(0.5, 0.8, 0), "NOT_QUALIFIED")
    eq(verdict_for(0.8, 0.8, 0), "QUALIFIED", "floor is inclusive")


def test_all_blocked_corpus_scores_zero_not_one():
    """Division-by-zero guard: an unmeasurable corpus is a failed swap."""
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    tools_only = [t for t in tasks if "tools" in t.requires]
    ok(tools_only, "fixture has a tool task")
    report = run_corpus(tools_only, _load(OFFLINE), MockTransport(FIXTURE), 0.80)
    eq(report["score"], 0.0, "score")
    eq(report["verdict"], "NOT_QUALIFIED", "verdict")


def test_report_excerpts_are_bounded_and_absent_on_pass():
    report = _run(OFFLINE)
    for task in report["tasks"]:
        if task["outcome"] == "passed":
            ok("excerpt" not in task, f"{task['id']} passed: no excerpt stored")
        ok(len(task.get("excerpt", "")) <= 200, f"{task['id']} excerpt within §7.3 bound")


def test_report_carries_corpus_hash_for_comparability():
    a, b = _run(PRIMARY), _run(OFFLINE)
    eq(a["corpus_hash"], b["corpus_hash"], "same corpus, same hash")
    eq(len(a["corpus_hash"]), 64, "sha256 hex")


# --- transport -------------------------------------------------------------

def test_missing_fixture_entry_raises_instead_of_scoring_zero():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "empty.json"
        empty.write_text("{}", encoding="utf-8")
        try:
            run_corpus(tasks, _load(PRIMARY), MockTransport(empty), 0.80)
        except TransportError:
            return
        raise AssertionError("a missing fixture entry must raise, not look like a failed task")


# --- swap ------------------------------------------------------------------

def test_swap_between_equals_is_compatible():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    result = compare(_load(PRIMARY), _load(FALLBACK), tasks)
    eq(result["capability_lost"], [], "no loss")
    eq(result["verdict"], "compatible", "verdict")


def test_swap_to_offline_is_incompatible_and_names_the_cost():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    result = compare(_load(PRIMARY), _load(OFFLINE), tasks)
    ok("tools" in result["capability_lost"], "tool loss reported")
    eq(result["context_delta"], 32768 - 200000, "context delta")
    eq(result["verdict"], "incompatible", "corpus work breaks")
    eq(result["corpus_impact"]["blocked_weight"], 5, "weight at risk")


def test_swap_without_corpus_degrades_rather_than_guessing():
    result = compare(_load(PRIMARY), _load(OFFLINE))
    eq(result["verdict"], "degraded", "no corpus means no evidence of breakage")


def test_swap_reports_sovereignty_change_without_judging_it():
    result = compare(_load(PRIMARY), _load(OFFLINE))
    delta = result["sovereignty_delta"]
    eq(delta["weights_portable"], {"from": False, "to": True}, "portability gain reported")
    eq(delta["data_region"], {"from": "us", "to": "self"}, "region change reported")


# --- CLI contract ----------------------------------------------------------

def test_cli_validate_exit_codes():
    eq(_cli("validate", str(PRIMARY)).returncode, 0, "valid manifest exits 0")
    bad = EXAMPLES / "manifests" / "invalid" / "001-inline-secret.json"
    eq(_cli("validate", str(bad)).returncode, 1, "invalid manifest exits 1")


def test_cli_eval_writes_schema_shaped_report():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "report.json"
        proc = _cli(
            "eval", "--manifest", str(OFFLINE), "--corpus", str(EXAMPLES / "tasks"),
            "--transport", "mock", "--fixture", str(FIXTURE), "--out", str(out),
        )
        eq(proc.returncode, 0, f"QUALIFIED_DEGRADED exits 0 (stderr: {proc.stderr})")
        report = json.loads(out.read_text(encoding="utf-8"))
        for key in ("report_version", "generated_at", "manifest_id", "corpus_hash",
                    "floor", "score", "verdict", "totals", "tasks"):
            ok(key in report, f"report carries {key}")
        eq(_cli("report", str(out)).returncode, 0, "stored report re-prints with its verdict")


def test_cli_eval_below_floor_exits_one():
    proc = _cli(
        "eval", "--manifest", str(OFFLINE), "--corpus", str(EXAMPLES / "tasks"),
        "--transport", "mock", "--fixture", str(FIXTURE), "--floor", "0.95",
    )
    eq(proc.returncode, 1, "NOT_QUALIFIED exits 1")


def test_cli_mock_without_fixture_is_usage_error_not_gate_failure():
    proc = _cli("eval", "--manifest", str(OFFLINE), "--corpus", str(EXAMPLES / "tasks"), "--transport", "mock")
    eq(proc.returncode, 2, "missing fixture is exit 2 — nothing was measured")


def test_cli_swap_exit_codes():
    eq(_cli("swap", "--from", str(PRIMARY), "--to", str(FALLBACK), "--corpus", str(EXAMPLES / "tasks")).returncode, 0)
    eq(_cli("swap", "--from", str(PRIMARY), "--to", str(OFFLINE), "--corpus", str(EXAMPLES / "tasks")).returncode, 1)


def test_cli_corpus_lint_passes_on_the_golden_corpus():
    proc = _cli("corpus", str(EXAMPLES / "tasks"))
    eq(proc.returncode, 0, "corpus lints clean")
    ok("below the 20-task floor" in proc.stdout, "P3 shortfall is stated, not hidden")


if __name__ == "__main__":
    sys.exit(run_suite(dict(globals()), "gate (offline)"))
