"""Block parser for BBE-STD-002 v1.0-RC2.

Stack-based; supports cross-type nesting; tracks parent labels for
same-type-nesting detection (BBE-COMM-021). Returns parsed blocks plus any
structural findings discovered during parse (BBE-COMM-001..003).
"""

from __future__ import annotations

from .constants import OPEN_TAG_RE, CLOSE_TAG_RE, HEADER_RE
from .model import Block, Finding


def parse_blocks(text: str) -> tuple[list[Block], list[Finding]]:
    """Extract STD-002 blocks from a text region.

    Returns (blocks, findings). Findings are structural-parse errors only
    (BBE-COMM-001 unmatched close, BBE-COMM-002 label mismatch, BBE-COMM-003
    unclosed). Per-block rules run separately in validator.py.
    """
    lines = text.split("\n")
    blocks: list[Block] = []
    findings: list[Finding] = []
    # Stack of (label, open_line, captured_lines)
    stack: list[tuple[str, int, list[tuple[int, str]]]] = []

    for ln, line in enumerate(lines, start=1):
        m_open = OPEN_TAG_RE.match(line)
        m_close = CLOSE_TAG_RE.match(line)

        if m_open:
            label = m_open.group(1)
            stack.append((label, ln, []))
            continue

        if m_close:
            label = m_close.group(1)
            if not stack:
                findings.append(Finding(
                    "BBE-COMM-001", "error", "§4.2",
                    f"Closing tag [/{label}] without matching opening tag",
                    ln,
                ))
                continue
            open_label, open_ln, captured = stack.pop()
            if open_label != label:
                findings.append(Finding(
                    "BBE-COMM-002", "error", "§4.2",
                    f"Closing tag [/{label}] does not match opening tag [{open_label}]",
                    ln, open_label,
                ))
            block = _build_block(open_label, open_ln, ln, captured)
            if stack:
                block.parent_label = stack[-1][0]
            blocks.append(block)
            continue

        if stack:
            stack[-1][2].append((ln, line))

    while stack:
        label, ln, _ = stack.pop()
        findings.append(Finding(
            "BBE-COMM-003", "error", "§4.2",
            f"Opening tag [{label}] without matching closing tag", ln, label,
        ))

    return blocks, findings


def _build_block(label: str, open_ln: int, close_ln: int,
                 captured: list[tuple[int, str]]) -> Block:
    headers: dict[str, str] = {}
    header_lines: dict[str, int] = {}
    body_lines: list[str] = []
    in_header = True
    body_start = close_ln  # default if body is empty

    for (ln, line) in captured:
        if in_header:
            if line.strip() == "" and not headers:
                continue  # leading blank lines before header
            if line.strip() == "":
                in_header = False
                body_start = ln
                continue
            m = HEADER_RE.match(line)
            if m:
                key = m.group(1)
                val = m.group(2).strip()
                headers[key] = val
                header_lines[key] = ln
                continue
            in_header = False
            body_start = ln
            body_lines.append(line)
        else:
            body_lines.append(line)

    return Block(
        label=label,
        open_line=open_ln,
        close_line=close_ln,
        headers=headers,
        header_lines=header_lines,
        body_text="\n".join(body_lines),
        body_start_line=body_start,
    )
