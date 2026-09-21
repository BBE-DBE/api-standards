"""Corpus validation, check semantics and hash stability (BBE-STD-004 §5, §7.3)."""

from __future__ import annotations

import copy
import json
import sys

from _harness import EXAMPLES, eq, has_finding, ok, run_suite

from bbe_port.tasks import corpus_hash, load_corpus, run_check, validate_task

VALID_TASK = json.loads((EXAMPLES / "tasks" / "01-extract-invoice-total.json").read_text(encoding="utf-8"))


def mutate(**changes):
    raw = copy.deepcopy(VALID_TASK)
    for key, value in changes.items():
        if value is None:
            raw.pop(key, None)
        else:
            raw[key] = value
    return raw


def test_valid_task_is_clean():
    eq(validate_task(copy.deepcopy(VALID_TASK)), [], "valid task")


def test_task_001_version():
    ok(has_finding(validate_task(mutate(task_version="0")), "BBE-TASK-001"), "bad task_version")


def test_task_002_required_and_unknown_fields():
    ok(has_finding(validate_task(mutate(prompt=None)), "BBE-TASK-002"), "missing prompt")
    ok(has_finding(validate_task(mutate(temperature=0.7)), "BBE-TASK-002"), "unknown field")
    ok(has_finding(validate_task(mutate(weight=0)), "BBE-TASK-002"), "weight below range")
    ok(has_finding(validate_task(mutate(weight=99)), "BBE-TASK-002"), "weight above range")


def test_task_003_id_shape():
    ok(has_finding(validate_task(mutate(id="Extract_Invoice")), "BBE-TASK-003"), "non-kebab id")


def test_task_004_check_shapes():
    ok(has_finding(validate_task(mutate(checks=[])), "BBE-TASK-004"), "empty checks")
    ok(has_finding(validate_task(mutate(checks=[{"type": "vibes"}])), "BBE-TASK-004"), "unknown type")
    ok(has_finding(validate_task(mutate(checks=[{"type": "contains_all"}])), "BBE-TASK-004"), "missing values")
    ok(has_finding(validate_task(mutate(checks=[{"type": "regex", "pattern": "("}])), "BBE-TASK-004"), "uncompilable regex")
    ok(has_finding(validate_task(mutate(checks=[{"type": "json_has_keys", "keys": []}])), "BBE-TASK-004"), "empty keys")


def test_task_005_requires_vocabulary():
    ok(has_finding(validate_task(mutate(requires=["telepathy"])), "BBE-TASK-005"), "unknown capability")
    ok(not has_finding(validate_task(mutate(requires=["tools", "vision"])), "BBE-TASK-005"), "known capabilities")


def test_check_contains_all():
    eq(run_check({"type": "contains_all", "values": ["1190", "RE-2026"]}, "Total 1190 on RE-2026-0417")[0], True)
    eq(run_check({"type": "contains_all", "values": ["1190", "missing"]}, "Total 1190")[0], False)


def test_check_is_case_insensitive():
    eq(run_check({"type": "contains_all", "values": ["TECHNIK"]}, "technik")[0], True)


def test_check_contains_any_and_not_contains():
    eq(run_check({"type": "contains_any", "values": ["a", "b"]}, "only b here")[0], True)
    eq(run_check({"type": "contains_any", "values": ["a", "b"]}, "neither")[0], False)
    eq(run_check({"type": "not_contains", "values": ["sk-"]}, "clean answer")[0], True)
    eq(run_check({"type": "not_contains", "values": ["sk-"]}, "here: sk-abc")[0], False)


def test_check_regex():
    eq(run_check({"type": "regex", "pattern": r"(?:Klausel|§)\s*\d+"}, "siehe Klausel 14.3")[0], True)
    eq(run_check({"type": "regex", "pattern": r"(?:Klausel|§)\s*\d+"}, "steht im Vertrag")[0], False)


def test_check_json_tolerates_fences_and_prose():
    fenced = 'Gerne:\n```json\n{"total_eur": 1190}\n```\n'
    eq(run_check({"type": "json_has_keys", "keys": ["total_eur"]}, fenced)[0], True)
    eq(run_check({"type": "json_has_keys", "keys": ["total_eur"]}, 'vorne {"total_eur": 1190} hinten')[0], True)
    eq(run_check({"type": "json_has_keys", "keys": ["total_eur"]}, "kein JSON hier")[0], False)


def test_check_equals_normalized():
    eq(run_check({"type": "equals_normalized", "value": "technik"}, "  Technik.  ")[0], True)
    eq(run_check({"type": "equals_normalized", "value": "technik"}, "technik und abrechnung")[0], False)


def test_golden_corpus_loads_clean():
    tasks, findings = load_corpus(EXAMPLES / "tasks")
    eq(findings, [], "corpus findings")
    eq(len(tasks), 8, "task count")
    eq(sum(t.weight for t in tasks), 20, "total weight")


def test_corpus_hash_is_order_and_keyorder_stable():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    baseline = corpus_hash(tasks)
    eq(corpus_hash(list(reversed(tasks))), baseline, "order independence")

    reordered = copy.deepcopy(tasks)
    reordered[0].raw = dict(reversed(list(reordered[0].raw.items())))
    eq(corpus_hash(reordered), baseline, "key-order independence")


def test_corpus_hash_changes_when_a_task_changes():
    tasks, _ = load_corpus(EXAMPLES / "tasks")
    baseline = corpus_hash(tasks)
    edited = copy.deepcopy(tasks)
    edited[0].raw["weight"] = edited[0].raw["weight"] + 1
    ok(corpus_hash(edited) != baseline, "hash must move when the corpus moves")


def test_missing_corpus_directory_is_a_finding():
    tasks, findings = load_corpus(EXAMPLES / "no-such-dir")
    eq(tasks, [], "no tasks")
    ok(has_finding(findings, "BBE-TASK-002"), "missing dir reported")


if __name__ == "__main__":
    sys.exit(run_suite(dict(globals()), "corpus + checks"))
