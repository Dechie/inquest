"""Documentation as first-class analysis input.

Documentation represents intended behavior and constraints. It is evidence
of intent, not automatically ground truth — it may be incomplete, stale, or
incorrect.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from codeanalyzer.domain.entities import Location


class DocRelationship(StrEnum):
    DESCRIBES = "describes"
    CONSTRAINTS = "constraints"
    WORKFLOW = "workflow"
    INVARIANT = "invariant"
    REQUIREMENT = "requirement"
    API_CONTRACT = "api_contract"
    RELATED = "related"


class DocumentationUnit(BaseModel):
    """A unit of documentation associated with a snapshot."""

    id: str
    snapshot_id: str
    source: str = Field(description="Path or identifier, e.g. docs/orders.md")
    location: Location | None = None
    title: str | None = None
    content: str
    kind: str | None = Field(
        default=None,
        description="readme | architecture | requirements | api | doc_comment | …",
    )
    entity_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class DocEntityLink(BaseModel):
    """Association between documentation and a program entity."""

    doc_id: str
    entity_id: str
    relationship: DocRelationship = DocRelationship.RELATED
