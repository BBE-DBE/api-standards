"""JSON-output helpers.

Renders Result envelopes into the wire format documented in
schemas/result.schema.json. Stable contract — breaking changes require a
schema MAJOR bump.
"""

from __future__ import annotations

import json
from typing import Any

from ..model import Result


RESULT_SCHEMA_VERSION = "1.0"


def to_json(result: Result, *, indent: int | None = 2) -> str:
    """Render a Result envelope as canonical JSON."""
    return json.dumps(result.to_dict(), indent=indent, sort_keys=False, ensure_ascii=False)
