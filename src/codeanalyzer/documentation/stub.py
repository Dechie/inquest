"""Stub DocumentationAPI for scaffolding and tests."""

from __future__ import annotations

from codeanalyzer.documentation.api import DocumentationAPI
from codeanalyzer.domain.documentation import DocumentationUnit
from codeanalyzer.domain.findings import Finding


class StubDocumentationAPI(DocumentationAPI):
    def get_docs(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def get_related_docs(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def get_documented_requirements(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def get_documented_invariants(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def get_documented_workflow(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def get_documented_constraints(self, entity_id: str) -> list[DocumentationUnit]:
        return []

    def find_docs_for_entities(self, entity_ids: list[str]) -> list[DocumentationUnit]:
        return []

    def find_docs_relevant_to_finding(self, finding: Finding) -> list[DocumentationUnit]:
        return []
