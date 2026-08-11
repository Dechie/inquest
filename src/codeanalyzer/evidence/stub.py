"""Stub EvidenceAPI for scaffolding and tests."""

from __future__ import annotations

from typing import Any

from codeanalyzer.domain.diagnostics import ExternalDiagnostic
from codeanalyzer.domain.entities import Entity, Relationship
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.evidence.api import EvidenceAPI


class StubEvidenceAPI(EvidenceAPI):
    """No-op evidence backend; all queries return empty / None."""

    def get_entity(self, entity_id: str) -> Entity | None:
        return None

    def get_file(self, file_id: str) -> Entity | None:
        return None

    def get_symbol(self, symbol_id: str) -> Entity | None:
        return None

    def get_references(self, symbol_id: str) -> list[Relationship]:
        return []

    def get_callers(self, function_id: str) -> list[Entity]:
        return []

    def get_callees(self, function_id: str) -> list[Entity]:
        return []

    def get_call_path(self, source_id: str, target_id: str) -> list[str] | None:
        return None

    def get_reachable_nodes(self, node_id: str) -> list[str]:
        return []

    def can_reach(self, source_id: str, target_id: str) -> bool:
        return False

    def get_entry_points(self, scope: LogicalSlice) -> list[Entity]:
        return []

    def get_exit_points(self, scope: LogicalSlice) -> list[Entity]:
        return []

    def get_control_flow(self, function_id: str) -> dict[str, Any]:
        return {}

    def get_paths(self, source_id: str, target_id: str) -> list[list[str]]:
        return []

    def get_dominators(self, node_id: str) -> list[str]:
        return []

    def get_post_dominators(self, node_id: str) -> list[str]:
        return []

    def get_branch_conditions(self, node_id: str) -> list[str]:
        return []

    def get_path_conditions(self, source_id: str, target_id: str) -> list[str]:
        return []

    def must_pass_through(self, source_id: str, target_id: str, node_id: str) -> bool:
        return False

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
