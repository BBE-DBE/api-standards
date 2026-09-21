"""Minimal test harness.

No pytest: the api-standards CI environment ships the standard library only
(same constraint that shaped bbe-comm). Each suite imports `run_suite` and
calls it with the module globals.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any, Dict

STD_ROOT = Path(__file__).resolve().parents[1]
TOOL_ROOT = STD_ROOT / "tools" / "bbe-port"
EXAMPLES = STD_ROOT / "examples"

sys.path.insert(0, str(TOOL_ROOT))


def eq(actual: Any, expected: Any, label: str = "") -> None:
    if actual != expected:
        raise AssertionError(f"{label or 'value'}: expected {expected!r}, got {actual!r}")


def ok(condition: Any, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def has_finding(findings, check_id: str) -> bool:
    return any(f.check_id == check_id for f in findings)


def run_suite(namespace: Dict[str, Any], title: str) -> int:
    tests = sorted(
        (name, fn) for name, fn in namespace.items()
        if name.startswith("test_") and callable(fn)
    )
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception:  # noqa: BLE001 - a test harness reports everything
            failed += 1
            print(f"  FAIL {name}")
            traceback.print_exc()
    passed = len(tests) - failed
    print(f"{title}: {passed}/{len(tests)} passed")
    return 1 if failed else 0
