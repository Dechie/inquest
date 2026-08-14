"""Provenance-bearing facts.

Every important fact entering the reasoning pipeline must retain provenance.

Two orthogonal dimensions are tracked separately:
  - ProvenanceKind  — *origin* (where did this come from?)
  - EpistemicStatus — *certainty* (how firmly established is it?)

Collapsing them into a single field was a known design debt; this module
maintains both explicitly. Existing code that only sets `kind` gets a
sensible `epistemic_status` default derived from the mapping in enums.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from codeanalyzer.domain.enums import EpistemicStatus, ProvenanceKind, default_epistemic_status


class Provenance(BaseModel):
    """Where a fact came from and how firmly it is established.

    `kind` captures origin; `epistemic_status` captures certainty.
    They are intentionally separate fields — do not conflate them.
    """

    kind: ProvenanceKind
    source: str = Field(
        description="Human-readable origin, e.g. 'OrderService.php:83' or 'docs/orders.md'"
    )
    epistemic_status: EpistemicStatus | None = Field(
        default=None,
        description=(
            "How firmly this fact is established. "
            "Defaults to the conventional status for `kind` when not supplied."
        ),
    )
    analyzer: str | None = Field(
        default=None,
        description="Analyzer id when kind is EXTERNAL_ANALYZER_FACT",
    )
    analyzer_version: str | None = None
    snapshot_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _fill_epistemic_status(self) -> "Provenance":
        """Populate epistemic_status from kind when not explicitly set."""
        if self.epistemic_status is None:
            self.epistemic_status = default_epistemic_status(self.kind)
        return self

    @property
    def is_high_confidence(self) -> bool:
        """True for facts that are observed or deterministically derived."""
        return self.epistemic_status in (EpistemicStatus.OBSERVED, EpistemicStatus.DERIVED)


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
        """Hypotheses and inferences must never be treated as authoritative graph structure."""
        return self.provenance.epistemic_status not in (
            EpistemicStatus.HYPOTHESIZED,
            EpistemicStatus.INFERRED,
        )

