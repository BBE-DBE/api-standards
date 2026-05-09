"""Lineage / correlation graph analysis.

Builds a directed graph from @parent_id and @refs edges, plus a separate
correlation map by @correlation_id. Detects cycles, orphan parent
references (parent_ids not present in the parsed text), and groups blocks
by correlation.

Exit code 3 is reserved for lineage errors.
"""

from __future__ import annotations

import json

from .model import Block, TraceResult, TraceEdge
from .parser import parse_blocks


def _parse_refs(raw: str) -> list[str]:
    raw = raw.strip()
    if raw.startswith("["):
        try:
            arr = json.loads(raw)
            if isinstance(arr, list):
                return [str(x) for x in arr]
        except json.JSONDecodeError:
            pass
    if "," in raw:
        return [x.strip().strip('"').strip("'") for x in raw.split(",") if x.strip()]
    return [raw]


def _detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Return cycles found via DFS. Each cycle is a list of node ids."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    on_path: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        if node in on_path:
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        on_path.add(node)
        path.append(node)
        for neighbour in graph.get(node, []):
            dfs(neighbour)
        path.pop()
        on_path.discard(node)

    for n in list(graph.keys()):
        if n not in visited:
            dfs(n)

    return cycles


def trace(text: str) -> TraceResult:
    blocks, _ = parse_blocks(text)
    nodes: list[str] = []
    edges: list[TraceEdge] = []
    correlation_groups: dict[str, list[str]] = {}

    block_ids: set[str] = set()
    for b in blocks:
        bid = b.headers.get("id")
        if bid:
            nodes.append(bid)
            block_ids.add(bid)
            corr = b.headers.get("correlation_id")
            if corr:
                correlation_groups.setdefault(corr, []).append(bid)
            parent = b.headers.get("parent_id")
            if parent:
                edges.append(TraceEdge(src=bid, dst=parent, kind="parent"))
            refs_raw = b.headers.get("refs")
            if refs_raw:
                for r in _parse_refs(refs_raw):
                    edges.append(TraceEdge(src=bid, dst=r, kind="ref"))

    # Adjacency for cycle detection: parent edges only (refs don't form
    # the spanning lineage tree; cycles in refs are merely cross-links)
    parent_graph: dict[str, list[str]] = {}
    for e in edges:
        if e.kind == "parent":
            parent_graph.setdefault(e.src, []).append(e.dst)

    cycles = _detect_cycles(parent_graph)

    # Orphans: parent ids not present in this text region
    orphans = sorted({e.dst for e in edges if e.kind == "parent" and e.dst not in block_ids})

    # ok-criterion: cycles are always errors; orphans are common when tracing
    # a single file (the parent often lives in a different conversation turn).
    # Orphans are reported but don't fail the trace.
    ok = len(cycles) == 0
    return TraceResult(
        nodes=nodes,
        edges=edges,
        cycles=cycles,
        orphans=orphans,
        correlation_groups=correlation_groups,
        ok=ok,
    )
