"""Provenance-bearing facts.

Every important fact entering the reasoning pipeline must retain provenance.
The system must preserve the distinction between observation, derivation,
external diagnostics, and semantic interpretation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import ProvenanceKind


class Provenance(BaseModel):
    """Where a fact came from and how it was obtained."""

    kind: ProvenanceKind
    source: str = Field(
        description="Human-readable origin, e.g. 'OrderService.php:83' or 'docs/orders.md'"
    )
    analyzer: str | None = Field(
        default=None,
        description="Analyzer id when kind is EXTERNAL_ANALYZER_FACT",
    )
    analyzer_version: str | None = None
    snapshot_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ProvenancedFact(BaseModel):
    """A single fact plus mandatory provenance metadata."""

    statement: str
    provenance: Provenance
    entity_ids: list[str] = Field(default_factory=list)
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence; hypotheses often carry uncertainty",
    )

    def is_authoritative_structure(self) -> bool:
        """Hypotheses must never be treated as authoritative graph structure."""
        return self.provenance.kind != ProvenanceKind.HYPOTHESIS
