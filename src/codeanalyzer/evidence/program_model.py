"""Evidence API backed by a program model and substrate-derived facts."""

from __future__ import annotations

from typing import Any

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.provenance import ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.tooling import ToolStatus
from codeanalyzer.evidence.api import EvidenceAPI
from codeanalyzer.program.algorithms.reachability import find_path
from codeanalyzer.program.in_memory import InMemoryProgramModel


class ProgramModelEvidenceAPI(EvidenceAPI):
    """Serve call-graph queries from a program model plus derived fact cache."""

    def __init__(self, model: InMemoryProgramModel | None = None) -> None:
        self._model = model
        self._path_cache: dict[tuple[str, str], list[str]] = {}
        self._reachability_cache: dict[tuple[str, str], bool] = {}
        self._tool_statuses: dict[str, ToolStatus] = {}

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

    def set_tool_statuses(self, statuses: list[ToolStatus]) -> None:
        """Register tool status information from the negotiation phase."""
        for status in statuses:
            self._tool_statuses[status.analyzer_id] = status

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

    def node_in_graph(self, node_id: str) -> bool:
        """Return True if *node_id* appears in at least one call edge."""
        if self._model is None:
            return False
        graph = self._model.call_graph()
        return bool(graph.callers(node_id) or graph.callees(node_id))

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

    def node_in_data_flow(self, node_id: str) -> bool:
        """Return True if *node_id* appears in at least one data-flow edge."""
        if self._model is None:
            return False
        graph = self._model.data_flow()
        return bool(graph.consumers(node_id) or graph.producers(node_id))

    def get_data_flow(self, source_id: str, target_id: str) -> list[dict[str, Any]]:
        """Return data-flow paths from *source_id* to *target_id*.

        Uses BFS over DataFlowGraph edges. Each entry is a dict with
        ``path`` (list of node IDs) and ``kind`` (edge kind along the path).
        Returns an empty list when no path exists or model is absent.
        """
        if self._model is None:
            return []
        graph = self._model.data_flow()

        # BFS — record (node, path_so_far)
        from collections import deque

        queue: deque[tuple[str, list[str]]] = deque([(source_id, [source_id])])
        visited: set[str] = {source_id}
        results: list[dict[str, Any]] = []

        while queue:
            node, path = queue.popleft()
            if node == target_id and len(path) > 1:
                results.append({"path": path, "kind": "data_flow"})
                continue  # keep searching for alternate paths up to a limit
            if len(results) >= 10:  # cap to avoid explosion
                break
            for consumer in graph.consumers(node):
                if consumer not in visited:
                    visited.add(consumer)
                    queue.append((consumer, path + [consumer]))

        return results

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
        """Return analyzer capabilities based on tool status from negotiation phase."""
        status = self._tool_statuses.get(analyzer_id)
        if status is None:
            return None
        return {
            "analyzer_id": status.analyzer_id,
            "executable": status.executable,
            "version": status.version,
            "project_requirement": status.project_requirement,
            "capabilities": {kind.value: state.value for kind, state in status.capabilities.items()},
            "failure": status.failure.value if status.failure else None,
            "is_usable": status.is_usable(),
        }
