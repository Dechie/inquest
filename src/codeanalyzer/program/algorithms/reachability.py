"""Reachability helpers (BFS/DFS) — not exposed to detectors or the LLM."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable


def bfs_reachable(
    start: str,
    neighbors: Callable[[str], list[str]],
) -> set[str]:
    """Return all nodes reachable from *start* via *neighbors*."""
    seen: set[str] = {start}
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in neighbors(node):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def find_path(
    source: str,
    target: str,
    neighbors: Callable[[str], list[str]],
) -> list[str] | None:
    """Return one path from source to target, or None."""
    if source == target:
        return [source]
    parent: dict[str, str | None] = {source: None}
    queue: deque[str] = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in neighbors(node):
            if nxt in parent:
                continue
            parent[nxt] = node
            if nxt == target:
                path = [target]
                cur: str | None = node
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                return path
            queue.append(nxt)
    return None
