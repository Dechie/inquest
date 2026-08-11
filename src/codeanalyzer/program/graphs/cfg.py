"""Control-flow graph — intra-function control flow."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CFGNode(BaseModel):
    id: str
    kind: str = "basic_block"  # entry | exit | basic_block | branch | …
    label: str | None = None
    location: str | None = None


class CFGEdge(BaseModel):
    source_id: str
    target_id: str
    condition: str | None = None


class ControlFlowGraph(BaseModel):
    """CFG for a single function/method."""

    function_id: str
    nodes: list[CFGNode] = Field(default_factory=list)
    edges: list[CFGEdge] = Field(default_factory=list)
    entry_id: str | None = None
    exit_ids: list[str] = Field(default_factory=list)

    def successors(self, node_id: str) -> list[str]:
        return [e.target_id for e in self.edges if e.source_id == node_id]

    def predecessors(self, node_id: str) -> list[str]:
        return [e.source_id for e in self.edges if e.target_id == node_id]
