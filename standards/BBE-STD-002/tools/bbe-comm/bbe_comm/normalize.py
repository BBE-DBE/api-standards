"""Welle-3 / Welt-A → RC2 mechanical normalization.

Applies textual transformations to convert legacy block forms into RC2-conformant
form. The output is reviewable text — never overwrites the input file.

Conversions applied:
  - `[<TYPE> v1.0]` → `[<TYPE>]` (drop tag-embedded version)
  - `key: value` headers (no @ prefix) → `@key: value` (when at the top of a block)
  - `session:` → `@correlation_id:` (Welt-A naming → RC2 naming)
  - `parent:` → `@parent_id:`
  - `<id>-2026-…T…:…:…Z-<hex>` → `<id>_…T…-…-…Z_<hex>` (filename-safe IDs)
  - mixed-case label `[Result-…]` → uppercase `[RESULT-…]`
  - `note: >` folded scalar → freeform body (the `>` line is dropped, indented continuation lines are de-indented)

The normalizer does NOT add `@bbe-comm` / `@type` if missing — those are
SEMANTIC additions that need operator awareness. It only normalizes shape.
"""

from __future__ import annotations

import re

_TAG_VERSION_RE = re.compile(r"^\[([A-Za-z][A-Za-z0-9_-]*)\s+v\d+\.\d+\]\s*$")
_TAG_CLOSE_LOWERCASE = re.compile(r"^\[/([A-Za-z][A-Za-z0-9_-]*)\]\s*$")
_LEGACY_HEADER_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$")
_LEGACY_ID_TIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}T)(\d{2}):(\d{2}):(\d{2})Z(\.[0-9]+Z)?"
)


def _normalize_label(label: str) -> str:
    """Uppercase + ensure pattern; replace internal lowercase with uppercase."""
    out = label.upper()
    return out


def _normalize_id_value(v: str) -> str:
    """Convert `op_auth-<ts-with-colons>-<hex>` to `op_auth_<ts-with-dashes>_<hex>`.

    Welt-A used `:` and `-` separators; RC2 uses `_` separator and `-` instead
    of `:` in the timestamp.
    """
    # Replace colons in time portion with dashes
    v = _LEGACY_ID_TIME_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}-{m.group(3)}-{m.group(4)}Z", v)
    # Convert outer separators: <slug>-<ts>-<hex> → <slug>_<ts>_<hex>
    # Only the OUTER dashes; the time-portion dashes stay. We use a heuristic:
    # change `-<ts-string>-` → `_<ts-string>_`.
    m = re.match(r"^([a-z][a-z0-9_]*)-(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z)-([a-f0-9]{4,8})$", v)
    if m:
        slug, ts, hex_suffix = m.group(1), m.group(2), m.group(3)
        # Pad hex to 8 chars if shorter
        if len(hex_suffix) < 8:
            hex_suffix = hex_suffix.rjust(8, "0")
        return f"{slug}_{ts}_{hex_suffix}"
    return v


# Welt-A → RC2 field-name renames
_FIELD_RENAMES = {
    "session": "correlation_id",
    "parent":  "parent_id",
}


def normalize_text(text: str) -> str:
    """Return a mechanically-converted RC2 form of `text`."""
    out_lines: list[str] = []
    in_block = False
    in_header = False
    skipping_folded = False
    folded_indent = 0

    for raw in text.split("\n"):
        line = raw

        # Strip tag-embedded version: [TYPE v1.0] → [TYPE]
        m_tagver = _TAG_VERSION_RE.match(line)
        if m_tagver:
            label = _normalize_label(m_tagver.group(1))
            line = f"[{label}]"
            in_block = True
            in_header = True
            out_lines.append(line)
            continue

        # Closing tag with lowercase mixed-case fix
        m_close = _TAG_CLOSE_LOWERCASE.match(line)
        if m_close:
            label = _normalize_label(m_close.group(1))
            line = f"[/{label}]"
            in_block = False
            in_header = False
            out_lines.append(line)
            continue

        # Tag without version (already RC2-ish or vanilla [LABEL])
        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1]
            if not inner.startswith("/"):
                in_block = True
                in_header = True
            label = inner[1:] if inner.startswith("/") else inner
            normalized = _normalize_label(label)
            line = f"[/{normalized}]" if inner.startswith("/") else f"[{normalized}]"
            out_lines.append(line)
            continue

        if in_block and in_header:
            # Skip Welt-A "note: >" folded scalars: emit as body text
            if skipping_folded:
                stripped = raw.strip()
                if not stripped:
                    skipping_folded = False
                    out_lines.append("")
                    continue
                # Indented continuation: de-indent
                if line.startswith("  "):
                    out_lines.append(line[2:])
                    continue
                else:
                    skipping_folded = False
                    # fall through to handle current line as new header/body

            stripped = raw.strip()
            if stripped == "":
                in_header = False
                out_lines.append("")
                continue

            # Already RC2 @-prefix? leave alone, possibly normalize id-shaped values
            if line.startswith("@"):
                m = re.match(r"^@([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", line)
                if m and m.group(1) in {"id", "parent_id"}:
                    line = f"@{m.group(1)}: {_normalize_id_value(m.group(2).strip())}"
                out_lines.append(line)
                continue

            # Welt-A "key: value" header (no @ prefix)
            m = _LEGACY_HEADER_RE.match(line)
            if m:
                key = m.group(1)
                val = m.group(2).strip()
                # Skip the YAML folded scalar pattern: "note: >" — rewrite as body
                if val == ">":
                    skipping_folded = True
                    in_header = False  # remainder is body
                    continue
                # Field rename
                key = _FIELD_RENAMES.get(key, key)
                # Value normalization for id-shaped fields
                if key in {"id", "parent_id"}:
                    val = _normalize_id_value(val)
                line = f"@{key}: {val}"
                out_lines.append(line)
                continue

            # Non-tag, non-header → body starts here
            in_header = False
            out_lines.append(line)
            continue

        out_lines.append(line)

    return "\n".join(out_lines)
