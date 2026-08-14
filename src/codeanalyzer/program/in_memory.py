"""In-memory program model for tests and minimal evidence backends."""

from __future__ import annotations

from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.program.graphs.call_graph import CallGraph
from codeanalyzer.program.graphs.cfg import ControlFlowGraph
from codeanalyzer.program.graphs.data_flow import DataFlowGraph
from codeanalyzer.program.model import ProgramModel


class InMemoryProgramModel(ProgramModel):
    """Snapshot-scoped program representation backed by in-memory structures."""

    def __init__(
        self,
        snapshot: Snapshot,
        *,
        entities: list[Entity] | None = None,
        relationships: list[Relationship] | None = None,
        call_graph: CallGraph | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._entities = {entity.id: entity for entity in (entities or [])}
        self._relationships = list(relationships or [])
        self._call_graph = call_graph or CallGraph()
        self._cfgs: dict[str, ControlFlowGraph] = {}

    @property
    def snapshot(self) -> Snapshot:
        return self._snapshot

    def entities(self) -> list[Entity]:
        return list(self._entities.values())

    def relationships(self) -> list[Relationship]:
        return list(self._relationships)

    def call_graph(self) -> CallGraph:
        return self._call_graph

    def cfg(self, function_id: str) -> ControlFlowGraph | None:
        return self._cfgs.get(function_id)

    def data_flow(self) -> DataFlowGraph:
        return DataFlowGraph()

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)
