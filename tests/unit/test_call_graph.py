"""Call graph and reachability tests."""

from __future__ import annotations

from codeanalyzer.program.algorithms.reachability import bfs_reachable, find_path
from codeanalyzer.program.graphs.call_graph import CallEdge, CallGraph


def test_call_graph_can_reach() -> None:
    graph = CallGraph(
        edges=[
            CallEdge(caller_id="A", callee_id="B"),
            CallEdge(caller_id="B", callee_id="C"),
        ]
    )
    assert graph.can_reach("A", "C")
    assert not graph.can_reach("C", "A")
    assert graph.callees("A") == ["B"]
    assert graph.callers("C") == ["B"]


def test_bfs_and_path() -> None:
    adj = {"A": ["B"], "B": ["C"], "C": []}

    def neighbors(n: str) -> list[str]:
        return adj.get(n, [])

    assert bfs_reachable("A", neighbors) == {"A", "B", "C"}
    assert find_path("A", "C", neighbors) == ["A", "B", "C"]
    assert find_path("C", "A", neighbors) is None
