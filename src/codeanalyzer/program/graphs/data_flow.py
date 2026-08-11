"""Data-flow graph — definition → transformation → use."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DataFlowEdge(BaseModel):
    source_id: str
    target_id: str
    kind: str = "flows_to"  # def_use | arg | return | field | …
    field: str | None = None


class DataFlowGraph(BaseModel):
    """Inter/intra-procedural data-flow relationships."""

    edges: list[DataFlowEdge] = Field(default_factory=list)

    def consumers(self, value_id: str) -> list[str]:
        return [e.target_id for e in self.edges if e.source_id == value_id]

    def producers(self, value_id: str) -> list[str]:
        return [e.source_id for e in self.edges if e.target_id == value_id]
