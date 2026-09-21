"""bbe-port command line interface (BBE-STD-004 §9).

Exit codes are the contract — CI reads them, humans read the text:
  0  gate passed / no findings
  1  gate failed (invalid manifest, incompatible swap, NOT_QUALIFIED)
  2  usage or transport error — the measurement did not happen
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Sequence

from . import STANDARD, __version__
from .constants import DEFAULT_FLOOR, MIN_CORPUS_SIZE_P3
from .manifest import Finding, load_manifest
from .swap import compare
from .tasks import corpus_hash, load_corpus
from .transports import TransportError, get_transport

EXIT_OK = 0
EXIT_GATE_FAILED = 1
EXIT_USAGE = 2


def _print_findings(findings: Sequence[Finding]) -> None:
    for finding in findings:
        print(f"  {finding}", file=sys.stderr)


def _load_floor(args: argparse.Namespace) -> float:
    if args.floor is not None:
        return float(args.floor)
    if args.policy:
        try:
            policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read policy {args.policy}: {exc}", file=sys.stderr)
            raise SystemExit(EXIT_USAGE)
        return float(policy.get("floor", DEFAULT_FLOOR))
    return DEFAULT_FLOOR


# --- subcommands -----------------------------------------------------------

def cmd_validate(args: argparse.Namespace) -> int:
    failures = 0
    for path in args.manifests:
        manifest, findings = load_manifest(path)
        if findings:
            failures += 1
            print(f"FAIL {path} ({len(findings)} finding(s))")
            _print_findings(findings)
        else:
            assert manifest is not None
            caps = ", ".join(sorted(c for c, on in manifest.capabilities().items() if on)) or "none"
            print(f"OK   {path} — {manifest.id} [{manifest.role}/{manifest.deployment}] caps: {caps}")
    return EXIT_GATE_FAILED if failures else EXIT_OK


def cmd_corpus(args: argparse.Namespace) -> int:
    tasks, findings = load_corpus(args.corpus)
    if findings:
        print(f"FAIL {args.corpus} ({len(findings)} finding(s))")
        _print_findings(findings)
        return EXIT_GATE_FAILED

    total_weight = sum(t.weight for t in tasks)
    print(f"OK   {args.corpus}")
    print(f"  tasks:  {len(tasks)} (weight {total_weight})")
    print(f"  hash:   {corpus_hash(tasks)}")
    categories: dict[str, int] = {}
    for task in tasks:
        categories[task.category] = categories.get(task.category, 0) + 1
    print("  categories: " + ", ".join(f"{k}={v}" for k, v in sorted(categories.items())))
    if len(tasks) < MIN_CORPUS_SIZE_P3:
        print(
            f"  NOTE: {len(tasks)} tasks is below the {MIN_CORPUS_SIZE_P3}-task floor for "
            f"conformance level P3 ({STANDARD} §3). Usable for development, not for a claim."
        )
    return EXIT_OK


def cmd_swap(args: argparse.Namespace) -> int:
    incumbent, findings_a = load_manifest(getattr(args, "from"))
    candidate, findings_b = load_manifest(args.to)
    if findings_a or findings_b:
        print("FAIL manifest validation")
        _print_findings([*findings_a, *findings_b])
        return EXIT_GATE_FAILED
    assert incumbent is not None and candidate is not None

    tasks = None
    if args.corpus:
        tasks, corpus_findings = load_corpus(args.corpus)
        if corpus_findings:
            print("FAIL corpus validation")
            _print_findings(corpus_findings)
            return EXIT_GATE_FAILED

    result = compare(incumbent, candidate, tasks)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"swap {result['from']} -> {result['to']}")
        print(f"  capability lost:   {', '.join(result['capability_lost']) or 'none'}")
        print(f"  capability gained: {', '.join(result['capability_gained']) or 'none'}")
        print(
            f"  context:           {result['context_from']} -> {result['context_to']} "
            f"({result['context_delta']:+d})"
        )
        if result["sovereignty_delta"]:
            for key, change in result["sovereignty_delta"].items():
                print(f"  sovereignty.{key}: {change['from']} -> {change['to']}")
        impact = result["corpus_impact"]
        if impact["corpus_size"]:
            print(
                f"  corpus impact:     {len(impact['blocked_tasks'])}/{impact['corpus_size']} tasks blocked "
                f"(weight {impact['blocked_weight']}/{impact['total_weight']})"
            )
            for blocked in impact["blocked_tasks"]:
                print(f"    - {blocked['id']}: {blocked['reason']}")
        print(f"  VERDICT: {result['verdict']}")
    return EXIT_GATE_FAILED if result["verdict"] == "incompatible" else EXIT_OK


def cmd_eval(args: argparse.Namespace) -> int:
    manifest, findings = load_manifest(args.manifest)
    if findings:
        print("FAIL manifest validation")
        _print_findings(findings)
        return EXIT_GATE_FAILED
    assert manifest is not None

    tasks, corpus_findings = load_corpus(args.corpus)
    if corpus_findings:
        print("FAIL corpus validation")
        _print_findings(corpus_findings)
        return EXIT_GATE_FAILED
    if not tasks:
        print(f"ERROR: corpus {args.corpus} contains no tasks", file=sys.stderr)
        return EXIT_USAGE

    kwargs = {"fixture": args.fixture} if args.transport == "mock" else {}
    if args.transport == "mock" and not args.fixture:
        print("ERROR: --transport mock requires --fixture", file=sys.stderr)
        return EXIT_USAGE

    try:
        transport = get_transport(args.transport, **kwargs)
    except TransportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE

    floor = _load_floor(args)

    from .runner import run_corpus  # deferred: keeps `validate` import-light

    try:
        report = run_corpus(tasks, manifest, transport, floor)
    except TransportError as exc:
        # Not a gate failure: nothing was measured.
        print(f"ERROR: transport failed: {exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return _emit_report(report, as_json=args.json, out=args.out)


def cmd_report(args: argparse.Namespace) -> int:
    try:
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read report {args.report}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return _emit_report(report, as_json=args.json, out=None)


def _emit_report(report: dict, as_json: bool, out: str | None) -> int:
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        totals = report["totals"]
        print(f"portability report — {report['manifest_id']} via {report.get('transport', '?')}")
        print(f"  corpus:  {report['corpus_size']} tasks @ {report['corpus_hash'][:16]}…")
        print(
            f"  results: {totals['passed']} passed / {totals['failed']} failed / "
            f"{totals['blocked']} blocked"
        )
        print(f"  score:   {report['score']:.2%} (floor {report['floor']:.0%})")
        for task in report["tasks"]:
            if task["outcome"] == "failed":
                print(f"    FAIL  {task['id']}: {'; '.join(task.get('failed_checks', []))}")
            elif task["outcome"] == "blocked":
                print(f"    BLOCK {task['id']}: {task.get('reason', '')}")
        print(f"  VERDICT: {report['verdict']}")
        if out:
            print(f"  written: {out}")
    return EXIT_OK if report["verdict"] != "NOT_QUALIFIED" else EXIT_GATE_FAILED


# --- entrypoint ------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bbe-port",
        description=f"{STANDARD} Model Provider Portability — manifest lint, swap check, portability gate.",
    )
    parser.add_argument("--version", action="version", version=f"bbe-port {__version__} ({STANDARD})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="lint provider manifests")
    p_validate.add_argument("manifests", nargs="+")
    p_validate.set_defaults(func=cmd_validate)

    p_corpus = sub.add_parser("corpus", help="lint a golden corpus directory")
    p_corpus.add_argument("corpus")
    p_corpus.set_defaults(func=cmd_corpus)

    p_swap = sub.add_parser("swap", help="compare incumbent vs candidate provider")
    p_swap.add_argument("--from", required=True, dest="from", metavar="MANIFEST")
    p_swap.add_argument("--to", required=True, metavar="MANIFEST")
    p_swap.add_argument("--corpus", help="corpus directory; enables corpus-impact analysis")
    p_swap.add_argument("--json", action="store_true")
    p_swap.set_defaults(func=cmd_swap)

    p_eval = sub.add_parser("eval", help="run the portability gate")
    p_eval.add_argument("--manifest", required=True)
    p_eval.add_argument("--corpus", required=True)
    p_eval.add_argument("--transport", default="mock", choices=["mock", "openai_chat"])
    p_eval.add_argument("--fixture", help="response fixture (required for --transport mock)")
    p_eval.add_argument("--floor", type=float, help=f"override the score floor (default {DEFAULT_FLOOR})")
    p_eval.add_argument("--policy", help="policy.json carrying the agreed floor")
    p_eval.add_argument("--out", help="write the report JSON here")
    p_eval.add_argument("--json", action="store_true")
    p_eval.set_defaults(func=cmd_eval)

    p_report = sub.add_parser("report", help="re-print a stored report and exit per its verdict")
    p_report.add_argument("report")
    p_report.add_argument("--json", action="store_true")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except SystemExit as exc:  # raised by _load_floor
        return int(exc.code or EXIT_USAGE)
    except BrokenPipeError:  # pragma: no cover
        return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
