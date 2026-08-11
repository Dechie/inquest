"""Documentation API protocol.

Documentation should be scoped to the logical slice and, more narrowly,
to the entities implicated by each finding.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.documentation import DocumentationUnit
from codeanalyzer.domain.findings import Finding


class DocumentationAPI(ABC):
    """Query interface for documentation / intent evidence."""

    @abstractmethod
    def get_docs(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def get_related_docs(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def get_documented_requirements(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def get_documented_invariants(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def get_documented_workflow(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def get_documented_constraints(self, entity_id: str) -> list[DocumentationUnit]: ...

    @abstractmethod
    def find_docs_for_entities(self, entity_ids: list[str]) -> list[DocumentationUnit]: ...

    @abstractmethod
    def find_docs_relevant_to_finding(self, finding: Finding) -> list[DocumentationUnit]: ...
