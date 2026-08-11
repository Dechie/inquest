"""Normalized program model facade."""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.program.graphs.call_graph import CallGraph
from codeanalyzer.program.graphs.cfg import ControlFlowGraph
from codeanalyzer.program.graphs.data_flow import DataFlowGraph


class ProgramModel(ABC):
    """Snapshot-scoped program representation used by evidence and scope engines."""

    @property
    @abstractmethod
    def snapshot(self) -> Snapshot: ...

    @abstractmethod
    def entities(self) -> list[Entity]: ...

    @abstractmethod
    def relationships(self) -> list[Relationship]: ...

    @abstractmethod
    def call_graph(self) -> CallGraph: ...

    @abstractmethod
    def cfg(self, function_id: str) -> ControlFlowGraph | None: ...

    @abstractmethod
    def data_flow(self) -> DataFlowGraph: ...

    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity | None: ...
