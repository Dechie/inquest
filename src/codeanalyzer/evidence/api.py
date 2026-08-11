"""Evidence API protocol.

Detectors consume semantic evidence queries rather than manipulating graph
internals. The LLM must not need to know whether BFS, DFS, or another
algorithm generated a fact.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.slices import LogicalSlice


class EvidenceAPI(ABC):
    """Semantic evidence queries over the program model and external diagnostics.

    Representative operations from the architecture baseline. Implementations
    may raise NotImplementedError for analyses not yet built.
    """

    # --- Entities & structure ---

    @abstractmethod
    def get_entity(self, entity_id: str) -> Entity | None: ...

    @abstractmethod
    def get_file(self, file_id: str) -> Entity | None: ...

    @abstractmethod
    def get_symbol(self, symbol_id: str) -> Entity | None: ...

    @abstractmethod
    def get_references(self, symbol_id: str) -> list[Relationship]: ...

    # --- Call graph ---

    @abstractmethod
    def get_callers(self, function_id: str) -> list[Entity]: ...

    @abstractmethod
    def get_callees(self, function_id: str) -> list[Entity]: ...

    @abstractmethod
    def get_call_path(self, source_id: str, target_id: str) -> list[str] | None: ...

    @abstractmethod
    def get_reachable_nodes(self, node_id: str) -> list[str]: ...

    @abstractmethod
    def can_reach(self, source_id: str, target_id: str) -> bool: ...

    # --- Control flow ---

    @abstractmethod
    def get_entry_points(self, scope: LogicalSlice) -> list[Entity]: ...

    @abstractmethod
    def get_exit_points(self, scope: LogicalSlice) -> list[Entity]: ...

    @abstractmethod
    def get_control_flow(self, function_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_paths(self, source_id: str, target_id: str) -> list[list[str]]: ...

    @abstractmethod
    def get_dominators(self, node_id: str) -> list[str]: ...

    @abstractmethod
    def get_post_dominators(self, node_id: str) -> list[str]: ...

    @abstractmethod
    def get_branch_conditions(self, node_id: str) -> list[str]: ...

    @abstractmethod
    def get_path_conditions(self, source_id: str, target_id: str) -> list[str]: ...

    @abstractmethod
    def must_pass_through(self, source_id: str, target_id: str, node_id: str) -> bool: ...

    # --- Data flow ---

    @abstractmethod
    def get_definitions(self, value_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_uses(self, value_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_reaching_definitions(self, use_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_data_flow(self, source_id: str, target_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_value_provenance(self, value_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_field_provenance(self, object_id: str, field: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_argument_flow(self, call_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_return_flow(self, function_id: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_object_shape(self, value_id: str) -> dict[str, Any]: ...

    @abstractmethod
    def get_field_consumers(self, object_id: str, field: str) -> list[Entity]: ...

    @abstractmethod
    def get_field_producers(self, object_id: str, field: str) -> list[Entity]: ...

    # --- External diagnostics ---

    @abstractmethod
    def get_external_diagnostics_for_entity(
        self, entity_id: str
    ) -> list[ExternalDiagnostic]: ...

    @abstractmethod
    def get_external_diagnostics_for_scope(
        self, scope: LogicalSlice
    ) -> list[ExternalDiagnostic]: ...

    @abstractmethod
    def get_diagnostic(
        self, rule_id: str, location: str
    ) -> ExternalDiagnostic | None: ...

    @abstractmethod
    def get_analyzer_capabilities(self, analyzer_id: str) -> dict[str, Any] | None: ...
