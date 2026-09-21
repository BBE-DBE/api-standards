"""Manifest validation — one positive and one negative per finding id,
plus dual-direction golden corpus over examples/manifests/."""

from __future__ import annotations

import copy
import json
import sys

from _harness import EXAMPLES, eq, has_finding, ok, run_suite

from bbe_port.manifest import load_manifest, validate_manifest

VALID = json.loads((EXAMPLES / "manifests" / "primary-saas.json").read_text(encoding="utf-8"))


def mutate(**changes):
    raw = copy.deepcopy(VALID)
    for key, value in changes.items():
        if value is None:
            raw.pop(key, None)
        else:
            raw[key] = value
    return raw


def test_valid_manifest_has_no_findings():
    eq(validate_manifest(copy.deepcopy(VALID)), [], "valid manifest")


def test_port_001_manifest_version():
    ok(has_finding(validate_manifest(mutate(manifest_version="2")), "BBE-PORT-001"), "bad version")
    ok(not has_finding(validate_manifest(copy.deepcopy(VALID)), "BBE-PORT-001"), "good version")


def test_port_002_required_field_missing():
    ok(has_finding(validate_manifest(mutate(role=None)), "BBE-PORT-002"), "missing role")


def test_port_003_id_shape_and_agreement():
    ok(has_finding(validate_manifest(mutate(id="not-a-pair")), "BBE-PORT-003"), "bad id shape")
    ok(has_finding(validate_manifest(mutate(vendor="openai")), "BBE-PORT-003"), "vendor mismatch")
    ok(has_finding(validate_manifest(mutate(model="other")), "BBE-PORT-003"), "model mismatch")


def test_port_004_rejects_inline_credentials():
    ok(
        has_finding(validate_manifest(mutate(credential_ref="sk-proj-Ab12Cd34Ef56Gh78Ij90Kl")), "BBE-PORT-004"),
        "inline key in credential_ref",
    )
    ok(
        has_finding(validate_manifest(mutate(notes="use Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")), "BBE-PORT-004"),
        "secret smuggled into notes",
    )
    ok(has_finding(validate_manifest(mutate(endpoint_env="https://api.example.com")), "BBE-PORT-004"), "URL in endpoint_env")
    for good in ("vault://llm/anthropic/api-key", "env:ANTHROPIC_API_KEY"):
        ok(not has_finding(validate_manifest(mutate(credential_ref=good)), "BBE-PORT-004"), f"accepts {good}")


def test_port_005_capabilities():
    caps = dict(VALID["capabilities"])
    ok(has_finding(validate_manifest(mutate(capabilities={**caps, "telepathy": True})), "BBE-PORT-005"), "unknown cap")
    ok(has_finding(validate_manifest(mutate(capabilities={**caps, "tools": "yes"})), "BBE-PORT-005"), "non-boolean cap")
    missing = {k: v for k, v in caps.items() if k != "tools"}
    ok(has_finding(validate_manifest(mutate(capabilities=missing)), "BBE-PORT-005"), "required cap missing")


def test_port_006_enums_and_sovereignty():
    ok(has_finding(validate_manifest(mutate(role="whatever")), "BBE-PORT-006"), "bad role")
    ok(has_finding(validate_manifest(mutate(wire="grpc")), "BBE-PORT-006"), "bad wire")
    ok(has_finding(validate_manifest(mutate(deployment="edge")), "BBE-PORT-006"), "bad deployment")
    sov = dict(VALID["sovereignty"])
    ok(has_finding(validate_manifest(mutate(sovereignty={**sov, "data_region": "Germany"})), "BBE-PORT-006"), "bad region")
    ok(has_finding(validate_manifest(mutate(sovereignty={**sov, "runs_offline": "no"})), "BBE-PORT-006"), "non-boolean flag")


def test_port_007_numeric_limits():
    ok(has_finding(validate_manifest(mutate(context_tokens=0)), "BBE-PORT-007"), "zero context")
    ok(has_finding(validate_manifest(mutate(context_tokens="200k")), "BBE-PORT-007"), "string context")
    ok(has_finding(validate_manifest(mutate(max_output_tokens=999999)), "BBE-PORT-007"), "output > context")
    bad_cost = {"input": -1, "output": 25.0, "currency": "GBP"}
    ok(has_finding(validate_manifest(mutate(cost_per_mtok=bad_cost)), "BBE-PORT-007"), "bad cost")


def test_port_008_unknown_field():
    ok(has_finding(validate_manifest(mutate(favourite_colour="purple")), "BBE-PORT-008"), "unknown field")


def test_capability_absent_optional_reads_false():
    manifest, findings = load_manifest(EXAMPLES / "manifests" / "offline-selfhosted.json")
    eq(findings, [], "offline manifest valid")
    eq(manifest.capability("vision"), False, "vision false")
    eq(manifest.capability("no_such_flag"), False, "unknown flag reads False, never raises")


def test_golden_corpus_valid_manifests_are_clean():
    for path in sorted((EXAMPLES / "manifests").glob("*.json")):
        _, findings = load_manifest(path)
        eq(findings, [], f"{path.name} should be clean")


def test_golden_corpus_invalid_manifests_all_fire():
    paths = sorted((EXAMPLES / "manifests" / "invalid").glob("*.json"))
    ok(len(paths) >= 4, "invalid corpus is populated")
    for path in paths:
        manifest, findings = load_manifest(path)
        ok(manifest is None, f"{path.name} must not load")
        ok(bool(findings), f"{path.name} must produce findings")


def test_malformed_json_is_a_finding_not_a_crash():
    manifest, findings = load_manifest(EXAMPLES / "manifests" / "does-not-exist.json")
    ok(manifest is None and has_finding(findings, "BBE-PORT-002"), "missing file reported")


if __name__ == "__main__":
    sys.exit(run_suite(dict(globals()), "manifest validation"))
