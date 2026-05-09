"""CLI entry point for bbe-comm.

Subcommands:
    lint, score, trace, explain, repair-suggest, normalize, emit,
    verify-hmac, incident-test, auth-check, integrate-guard,
    learn (observe | suggest), report (stub), adapt (stub)

Universal flags: --json, --quiet
Exit codes: 0 success / 1 lint failed / 2 security violation /
            3 lineage error / 4 auth-inference attempt / 5 runtime error
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import (
    PACKAGE_VERSION, lint, score, trace,
    auth_check, incident_test,
)
from .model import Result
from .repair import repair_suggestions
from .normalize import normalize_text
from .integrations.json_output import to_json, RESULT_SCHEMA_VERSION
from .integrations.aguard import build_envelope
from .integrations.std002_blocks import emit as emit_block
from .learning import LearningStore, LearningEvent, EVENT_TYPES


# --- Result envelope helpers -----------------------------------------------

def _make_result(subcommand: str, file: str | None, blocks_count: int = 0,
                 exit_code: int = 0) -> Result:
    return Result(
        schema_version=RESULT_SCHEMA_VERSION,
        bbe_comm_version=PACKAGE_VERSION,
        subcommand=subcommand,
        file=file,
        blocks=blocks_count,
        exit_code=exit_code,
    )


def _output(result: Result, args: argparse.Namespace) -> None:
    if args.json:
        print(to_json(result))
    else:
        _output_text(result, args)


def _output_text(result: Result, args: argparse.Namespace) -> None:
    file_label = result.file or "<input>"
    head = f"\n{file_label}: subcommand={result.subcommand} blocks={result.blocks}"
    if result.findings:
        errs = [f for f in result.findings if f.severity == "error"]
        warns = [f for f in result.findings if f.severity == "warning"]
        head += f" errors={len(errs)} warnings={len(warns)}"
    if not args.quiet or result.findings or result.exit_code != 0:
        print(head)
    for f in result.findings:
        block = f" [{f.block_label}]" if f.block_label else ""
        print(f"  {f.severity.upper():7s} {f.check_id} {f.section} L{f.line}{block}: {f.message}")
    for s in result.scores:
        decl = f"declared L{s.declared_level}" if s.declared_level is not None else "no @compliance_level"
        warn = "  OVER-CLAIM!" if s.over_claim else ""
        print(f"  [{s.block_label}] type={s.block_type} computed=L{s.computed_level} {decl}{warn}")
        print(f"    {s.rationale}")
    if result.trace and not args.quiet:
        t = result.trace
        print(f"  trace: nodes={len(t.nodes)} edges={len(t.edges)} cycles={len(t.cycles)} orphans={len(t.orphans)}")
        if t.cycles:
            for c in t.cycles:
                print(f"    CYCLE: {' → '.join(c)}")
        if t.orphans:
            print(f"    orphans: {', '.join(t.orphans)}")
        if t.correlation_groups:
            for k, v in sorted(t.correlation_groups.items()):
                print(f"    correlation '{k}': {len(v)} block(s)")
    if result.auth and not args.quiet:
        a = result.auth
        print(f"  auth-check: verdict={a.verdict} auth_blocks={a.operator_auth_count}")
        for ev in a.inference_evidence:
            print(f"    inference cue: {ev}")
    if result.incident and not args.quiet:
        i = result.incident
        print(f"  incident-test: verdict={i.verdict} pattern_detected={i.pattern_detected} authorizing_block={i.has_authorizing_block}")
        for m in i.matches:
            print(f"    L{m['line']} '{m['phrase']}' (in {m.get('in_type') or 'free-prose'})")
    for s in result.suggestions:
        print(f"  REPAIR [{s.fix_kind} confidence={s.confidence}] {s.finding.check_id}: {s.description}")
        print(f"    hint: {s.patch_hint}")
    if result.extra and not args.quiet:
        for k, v in result.extra.items():
            print(f"  {k}: {v}")


# --- Subcommand handlers ---------------------------------------------------

def _read_files(paths: list[str]) -> list[tuple[str, str]]:
    """Return list of (path-as-str, content). Errors raise FileNotFoundError."""
    out: list[tuple[str, str]] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(p)
        out.append((str(path), path.read_text(encoding="utf-8")))
    return out


def cmd_lint(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        blocks, findings = lint(text, path)
        result = _make_result("lint", path, len(blocks))
        result.findings = findings
        errors = [f for f in findings if f.severity == "error"]
        warnings = [f for f in findings if f.severity == "warning"]
        if errors:
            result.exit_code = 1
            rc = max(rc, 1)
        elif warnings:
            result.exit_code = 2
            rc = max(rc, 2)
        _output(result, args)
    return rc


def cmd_score(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        blocks, _ = lint(text, path)
        result = _make_result("score", path, len(blocks))
        result.scores = score(text)
        if any(s.over_claim for s in result.scores):
            result.exit_code = 1
            rc = max(rc, 1)
        _output(result, args)
    return rc


def cmd_trace(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        blocks, _ = lint(text, path)
        t = trace(text)
        result = _make_result("trace", path, len(blocks))
        result.trace = t
        if not t.ok:
            result.exit_code = 3
            rc = max(rc, 3)
        _output(result, args)
    return rc


def cmd_explain(args: argparse.Namespace) -> int:
    """Pretty-print a check's explanation."""
    cid = args.check_id.upper()
    # Inline the registry — keep cli.py self-contained.
    explanations = {
        "BBE-COMM-001": "Closing tag without opening. Make sure every `[/LABEL]` has a matching `[LABEL]` before it.",
        "BBE-COMM-002": "Closing tag label does not match opening tag. Labels are byte-identical.",
        "BBE-COMM-003": "Opening tag without closing. Add `[/LABEL]` to close.",
        "BBE-COMM-004": "Label pattern violation. Labels match `^[A-Z][A-Z0-9_-]*$`.",
        "BBE-COMM-005": "Missing required `@bbe-comm` header. Add `@bbe-comm: 1.0` as the first header.",
        "BBE-COMM-006": "Missing required `@type` header. See RC2 §5.4 for the registry.",
        "BBE-COMM-007": "@bbe-comm value not in semver MAJOR.MINOR[.PATCH] form.",
        "BBE-COMM-008": "@bbe-comm major version unsupported. v1.x is supported in v1.0-RC2.",
        "BBE-COMM-009": "@type not in canonical registry and not in `x-<vendor>-<type>` form.",
        "BBE-COMM-010": "@status value out of registered set for this @type (warning).",
        "BBE-COMM-011": "@id pattern violation. Canonical: `<type-slug>_<YYYY-MM-DDTHH-MM-SSZ>_<hex8>`.",
        "BBE-COMM-012": "@id type-slug does not match @type (warning, see RC2 §6.2).",
        "BBE-COMM-013": "Non-root non-prompt block at L4+ missing @parent_id. Lineage integrity required.",
        "BBE-COMM-014": "@parent_id pattern violation.",
        "BBE-COMM-015": "operator_auth missing required field(s). Use `bbe-block sign auth` to emit.",
        "BBE-COMM-016": "ANTI-INFERENCE rule. Field names @authorize / @authorized / @authorization / @authority forbidden outside operator_auth (RC2 §7.4).",
        "BBE-COMM-017": "Custom header lacks @x- extension prefix.",
        "BBE-COMM-018": "@x- extension does not follow @x-<vendor>-<field> form (warning).",
        "BBE-COMM-019": "@compliance_level not in L0..L5.",
        "BBE-COMM-020": "Header-shaped line in body — header must be contiguous at top (warning).",
        "BBE-COMM-021": "Same-type nesting forbidden (lineage ambiguity).",
        "BBE-COMM-022": "Auth-only field used outside its allowed type (e.g. @hmac on operator_prompt).",
        "BBE-COMM-023": "Declared @compliance_level exceeds computed. RC2: HMAC alone is L4, not L5.",
        "BBE-COMM-024": "Scope token outside canonical vocabulary (RC2 §7.3).",
        "BBE-COMM-025": "@ttl exceeds policy max (1h).",
        "BBE-COMM-026": "@scope_mode value must be 'all' or 'any' (RC2 §7.3 multi-scope semantics).",
    }
    text = explanations.get(cid)
    if not text:
        print(f"unknown check-id: {args.check_id}", file=sys.stderr)
        return 5
    print(f"{cid}\n  {text}\n  Spec: see BBE-STD-002-v1.0-RC2.md and ADRs in docs/adr/.")
    return 0


def cmd_repair_suggest(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        blocks, findings = lint(text, path)
        result = _make_result("repair-suggest", path, len(blocks))
        result.findings = findings
        result.suggestions = repair_suggestions(findings)
        if [f for f in findings if f.severity == "error"]:
            result.exit_code = 1
            rc = max(rc, 1)
        _output(result, args)
    return rc


def cmd_normalize(args: argparse.Namespace) -> int:
    for path, text in _read_files(args.files):
        out = normalize_text(text)
        if args.json:
            print(json.dumps({"file": path, "normalized": out}, ensure_ascii=False))
        else:
            print(out)
    return 0


def cmd_emit(args: argparse.Namespace) -> int:
    try:
        out = emit_block(
            args.type,
            label=args.label,
            correlation_id=args.correlation,
            agent=args.agent,
            parent_id=args.parent,
        )
    except ValueError as e:
        print(f"emit: {e}", file=sys.stderr)
        return 5
    print(out, end="")
    return 0


def cmd_verify_hmac(args: argparse.Namespace) -> int:
    """Delegate to bbe-block-cli.sh `verify` subcommand if present.

    bbe-comm itself does not handle the op-secret. The runtime CLI does.
    """
    cli_path = os.environ.get("BBE_BLOCK_CLI")
    if not cli_path:
        # Try sibling tools/bbe-block-cli.sh
        guess = Path(__file__).resolve().parents[2] / "bbe-block-cli.sh"
        if guess.exists():
            cli_path = str(guess)
    if not cli_path or not Path(cli_path).exists():
        print("verify-hmac: bbe-block-cli.sh not found. Set $BBE_BLOCK_CLI or install at "
              "tools/bbe-block-cli.sh.", file=sys.stderr)
        return 5
    proc = subprocess.run([cli_path, "verify", "--file", args.file],
                          capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def cmd_incident_test(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        i = incident_test(text)
        result = _make_result("incident-test", path, 0, exit_code=i.exit_code)
        result.incident = i
        rc = max(rc, i.exit_code)
        _output(result, args)
    return rc


def cmd_auth_check(args: argparse.Namespace) -> int:
    rc = 0
    for path, text in _read_files(args.files):
        a = auth_check(text)
        result = _make_result("auth-check", path, 0, exit_code=a.exit_code)
        result.auth = a
        rc = max(rc, a.exit_code)
        _output(result, args)
    return rc


def cmd_integrate_guard(args: argparse.Namespace) -> int:
    """Build an AGUARD-decision-envelope JSON from a file's blocks/findings."""
    for path, text in _read_files(args.files):
        blocks, findings = lint(text, path)
        envelope = build_envelope(blocks, findings, file=path,
                                  correlation_id=args.correlation,
                                  subcommand="integrate-guard")
        # AGUARD envelope is its own contract — emit as raw JSON, not nested in Result
        print(json.dumps(envelope, indent=2 if not args.json else None, ensure_ascii=False))
    return 0


def cmd_learn(args: argparse.Namespace) -> int:
    store_dir = args.store or _default_store_dir()
    store = LearningStore(store_dir)
    if args.learn_action == "observe":
        try:
            payload = json.loads(args.event_json)
        except json.JSONDecodeError as e:
            print(f"learn observe: invalid JSON: {e}", file=sys.stderr)
            return 5
        # Build event from payload — only known fields are honoured
        evt = LearningEvent(**{k: v for k, v in payload.items()
                               if k in LearningEvent.__dataclass_fields__})
        if not evt.event_type:
            print(f"learn observe: missing event_type (allowed: {sorted(EVENT_TYPES)})",
                  file=sys.stderr)
            return 5
        try:
            store.observe(evt)
        except ValueError as e:
            print(f"learn observe: {e}", file=sys.stderr)
            return 5
        print(f"learn: observed {evt.event_type}")
        return 0
    if args.learn_action == "suggest":
        suggestions = store.synthesize_suggestions(min_count=args.min_count)
        if args.json:
            print(json.dumps(suggestions, indent=2, ensure_ascii=False))
        else:
            print(f"learn: synthesized {len(suggestions)} suggestion(s)")
            for s in suggestions:
                print(f"  - {s['title']} → {s['target_file']}")
        return 0
    print(f"learn: unknown action {args.learn_action!r}", file=sys.stderr)
    return 5


def cmd_report(args: argparse.Namespace) -> int:
    """ROADMAP — issue a multi-block correlation report.

    Interface defined: input is a glob of files (or a directory); output is a
    Markdown report that lists every block with a given @correlation_id, in
    lineage order. Implementation deferred to v1.1 (ADR-0001 §6).
    """
    print("report: ROADMAP — interface defined; implementation deferred to v1.1.\n"
          "  See docs/adr/0001-self-optimization-learning-loop.md §6.",
          file=sys.stderr)
    return 5


def cmd_adapt(args: argparse.Namespace) -> int:
    """ROADMAP — propose process adaptations from learning store.

    Interface defined: scan learning store, propose new test cases / new
    rules / schema additions as `tools/bbe-comm/suggestions/*.md`. ALL
    output is review-only. No silent mutations. Deferred to v1.1.
    """
    print("adapt: ROADMAP — use `bbe-comm learn suggest` for the v1.0-RC2 surface.\n"
          "  Adaptive proposals deferred to v1.1.", file=sys.stderr)
    return 5


def _default_store_dir() -> str:
    here = Path(__file__).resolve().parents[1]
    return str(here / "data")


# --- Argparse setup --------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    # Universal flags available BOTH before and after the subcommand.
    # We declare them on a "parents" parser and attach to every subparser.
    universal = argparse.ArgumentParser(add_help=False)
    universal.add_argument("--json", action="store_true",
                           help="machine-readable output")
    universal.add_argument("--quiet", action="store_true",
                           help="suppress clean files")

    p = argparse.ArgumentParser(
        prog="bbe-comm",
        description=f"BBE Communication Intelligence Tool (BBE-STD-002 v1.0-RC2, package {PACKAGE_VERSION})",
        parents=[universal],
    )
    p.add_argument("--version", action="version", version=f"bbe-comm {PACKAGE_VERSION}")

    sub = p.add_subparsers(dest="cmd", required=True)
    # Re-use the universal parser as a parent for every subcommand so flags
    # like `bbe-comm lint file.txt --quiet` (flag-after-positional) work too.
    _U = [universal]

    # lint
    sp = sub.add_parser("lint", parents=_U, help="validate STD-002 blocks")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_lint)

    # score
    sp = sub.add_parser("score", parents=_U, help="compute L0..L5 per block")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_score)

    # trace
    sp = sub.add_parser("trace", parents=_U, help="check parent_id / correlation chains")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_trace)

    # explain
    sp = sub.add_parser("explain", parents=_U, help="explain a BBE-COMM-NNN check")
    sp.add_argument("check_id", help="e.g. BBE-COMM-016")
    sp.set_defaults(func=cmd_explain)

    # repair-suggest
    sp = sub.add_parser("repair-suggest", parents=_U, help="propose minimal fixes for findings")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_repair_suggest)

    # normalize
    sp = sub.add_parser("normalize", parents=_U, help="Welle-3 / Welt-A → RC2 mechanical convert")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_normalize)

    # emit
    sp = sub.add_parser("emit", parents=_U, help="print a template block for a given @type")
    sp.add_argument("type", choices=["operator_prompt", "operator_auth", "operator_deny",
                                     "agent_query", "agent_result", "agent_abort"])
    sp.add_argument("--label")
    sp.add_argument("--correlation")
    sp.add_argument("--agent")
    sp.add_argument("--parent")
    sp.set_defaults(func=cmd_emit)

    # verify-hmac
    sp = sub.add_parser("verify-hmac", parents=_U, help="verify HMAC via bbe-block-cli.sh")
    sp.add_argument("file")
    sp.set_defaults(func=cmd_verify_hmac)

    # incident-test
    sp = sub.add_parser("incident-test", parents=_U, help="detect prose-only auth-inference attempts")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_incident_test)

    # auth-check
    sp = sub.add_parser("auth-check", parents=_U, help="audit a region for prose-vs-block authorization")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_auth_check)

    # integrate-guard
    sp = sub.add_parser("integrate-guard", parents=_U, help="emit AGUARD decision envelope JSON")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--correlation")
    sp.set_defaults(func=cmd_integrate_guard)

    # learn
    sp = sub.add_parser("learn", parents=_U, help="self-optimization learning loop")
    learn_sub = sp.add_subparsers(dest="learn_action", required=True)
    obs = learn_sub.add_parser("observe", parents=_U, help="append a learning event")
    obs.add_argument("event_json", help="JSON object with at minimum {event_type: ...}")
    obs.add_argument("--store", help="learning-store directory (default tools/bbe-comm/data/)")
    sug = learn_sub.add_parser("suggest", parents=_U, help="synthesize suggestion files")
    sug.add_argument("--min-count", type=int, default=5)
    sug.add_argument("--store")
    sp.set_defaults(func=cmd_learn)

    # report (roadmap)
    sp = sub.add_parser("report", parents=_U, help="ROADMAP — multi-block correlation report")
    sp.add_argument("correlation_id")
    sp.set_defaults(func=cmd_report)

    # adapt (roadmap)
    sp = sub.add_parser("adapt", parents=_U, help="ROADMAP — synthesize process adaptations")
    sp.set_defaults(func=cmd_adapt)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        print(f"error: file not found: {e}", file=sys.stderr)
        return 5
    except KeyboardInterrupt:
        return 5


if __name__ == "__main__":
    sys.exit(main())
