"""Deterministic replay transport — the one the CI gate uses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..manifest import Manifest
from . import Completion, TransportError


class MockTransport:
    """Replays canned responses from a fixture file.

    Fixture shape:

        {
          "<manifest id>": { "<task id>": "response text" },
          "default":       { "<task id>": "response text" }
        }

    A missing entry raises rather than returning an empty string: a silent ""
    would be scored as a failed task and misreport a broken fixture as a bad
    model.
    """

    name = "mock"

    def __init__(self, fixture: str | Path):
        path = Path(fixture)
        try:
            self._data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise TransportError(f"fixture not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise TransportError(f"malformed fixture {path}: {exc}") from exc
        if not isinstance(self._data, dict):
            raise TransportError(f"fixture {path} must be a JSON object")
        self._fixture_path = path

    def complete(self, manifest: Manifest, system: str | None, prompt: str, task_id: str) -> Completion:
        for key in (manifest.id, "default"):
            bucket = self._data.get(key)
            if isinstance(bucket, dict) and task_id in bucket:
                text = bucket[task_id]
                if not isinstance(text, str):
                    raise TransportError(f"fixture {self._fixture_path}: {key}.{task_id} must be a string")
                return Completion(
                    text=text,
                    input_tokens=len(prompt) // 4,
                    output_tokens=len(text) // 4,
                    latency_ms=0,
                )
        raise TransportError(
            f"fixture {self._fixture_path} has no response for manifest {manifest.id!r} task {task_id!r}"
        )
