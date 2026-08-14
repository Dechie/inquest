"""Evidence API backed by a program model and substrate-derived facts."""

from __future__ import annotations

from typing import Any

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.provenance import ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.evidence.api import EvidenceAPI
from codeanalyzer.program.algorithms.reachability import find_path
from codeanalyzer.program.in_memory import InMemoryProgramModel


class ProgramModelEvidenceAPI(EvidenceAPI):
    """Serve call-graph queries from a program model plus derived fact cache."""

    def __init__(self, model: InMemoryProgramModel | None = None) -> None:
        self._model = model
        self._path_cache: dict[tuple[str, str], list[str]] = {}
        self._reachability_cache: dict[tuple[str, str], bool] = {}

    @property
    def model(self) -> InMemoryProgramModel | None:
        return self._model

    def apply_facts(self, facts: list[ProvenancedFact]) -> None:
        """Register facts produced by the analysis substrate."""
        for fact in facts:
            if len(fact.entity_ids) < 2:
                continue
            source_id = fact.entity_ids[0]
            target_id = fact.entity_ids[-1]
            if fact.statement.startswith("call_path:"):
                self._path_cache[(source_id, target_id)] = list(fact.entity_ids)
            elif fact.statement.startswith("reachability:"):
                self._reachability_cache[(source_id, target_id)] = True

    def get_entity(self, entity_id: str) -> Entity | None:
        if self._model is None:
            return None
        return self._model.get_entity(entity_id)

    def get_file(self, file_id: str) -> Entity | None:
        return self.get_entity(file_id)

    def get_symbol(self, symbol_id: str) -> Entity | None:
        return self.get_entity(symbol_id)

    def get_references(self, symbol_id: str) -> list[Relationship]:
        if self._model is None:
            return []
        return [rel for rel in self._model.relationships() if rel.source_id == symbol_id]

    def get_callers(self, function_id: str) -> list[Entity]:
        if self._model is None:
            return []
        return [
            entity
            for caller_id in self._model.call_graph().callers(function_id)
            if (entity := self._model.get_entity(caller_id)) is not None
        ]

    def get_callees(self, function_id: str) -> list[Entity]:
        if self._model is None:
            return []
        return [
            entity
            for callee_id in self._model.call_graph().callees(function_id)
            if (entity := self._model.get_entity(callee_id)) is not None
        ]

    def get_call_path(self, source_id: str, target_id: str) -> list[str] | None:
        cached = self._path_cache.get((source_id, target_id))
        if cached is not None:
            return cached
        if self._model is None:
            return None
        return find_path(
            source_id,
            target_id,
            self._model.call_graph().callees,
        )

    def get_reachable_nodes(self, node_id: str) -> list[str]:
        if self._model is None:
            return []
        graph = self._model.call_graph()
        seen: set[str] = set()
        stack = [node_id]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(graph.callees(node))
        return sorted(seen)

    def can_reach(self, source_id: str, target_id: str) -> bool:
        cached = self._reachability_cache.get((source_id, target_id))
        if cached is not None:
            return cached
        if self._model is None:
            return False
        return self._model.call_graph().can_reach(source_id, target_id)

    def get_entry_points(self, scope: LogicalSlice) -> list[Entity]:
        return []

    def get_exit_points(self, scope: LogicalSlice) -> list[Entity]:
        return []

    def get_control_flow(self, function_id: str) -> dict[str, Any]:
        return {}

    def get_paths(self, source_id: str, target_id: str) -> list[list[str]]:
        path = self.get_call_path(source_id, target_id)
        return [path] if path else []

    def get_dominators(self, node_id: str) -> list[str]:
        return []

    def get_post_dominators(self, node_id: str) -> list[str]:
        return []

    def get_branch_conditions(self, node_id: str) -> list[str]:
        return []

    def get_path_conditions(self, source_id: str, target_id: str) -> list[str]:
        return []

    def must_pass_through(self, source_id: str, target_id: str, node_id: str) -> bool:
        path = self.get_call_path(source_id, target_id)
        return path is not None and node_id in path

    def get_definitions(self, value_id: str) -> list[dict[str, Any]]:
        return []

    def get_uses(self, value_id: str) -> list[dict[str, Any]]:
        return []

    def get_reaching_definitions(self, use_id: str) -> list[dict[str, Any]]:
        return []

    def get_data_flow(self, source_id: str, target_id: str) -> list[dict[str, Any]]:
        return []

    def get_value_provenance(self, value_id: str) -> list[dict[str, Any]]:
        return []

    def get_field_provenance(self, object_id: str, field: str) -> list[dict[str, Any]]:
        return []

    def get_argument_flow(self, call_id: str) -> list[dict[str, Any]]:
        return []

    def get_return_flow(self, function_id: str) -> list[dict[str, Any]]:
        return []

    def get_object_shape(self, value_id: str) -> dict[str, Any]:
        return {}

    def get_field_consumers(self, object_id: str, field: str) -> list[Entity]:
        return []

    def get_field_producers(self, object_id: str, field: str) -> list[Entity]:
        return []

    def get_external_diagnostics_for_entity(
        self, entity_id: str
    ) -> list[ExternalDiagnostic]:
        return []

    def get_external_diagnostics_for_scope(
        self, scope: LogicalSlice
    ) -> list[ExternalDiagnostic]:
        return []

    def get_diagnostic(self, rule_id: str, location: str) -> ExternalDiagnostic | None:
        return None

    def get_analyzer_capabilities(self, analyzer_id: str) -> dict[str, Any] | None:
        return None
