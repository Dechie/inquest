"""Correctness properties and contracts (architecture Layer 6).

Properties describe what should hold; detectors evaluate them against evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import PropertyKind, PropertySource
from codeanalyzer.domain.provenance import Provenance


class CorrectnessProperty(BaseModel):
    """An intended correctness constraint over program behavior."""

    id: str
    snapshot_id: str
    slice_id: str | None = None
    kind: PropertyKind
    statement: str = Field(
        description="Human-readable property, e.g. 'reserve(order) must precede persist(order)'"
    )
    source: PropertySource
    scope_entity_ids: list[str] = Field(default_factory=list)
    formalization: dict[str, Any] | None = Field(
        default=None,
        description="Optional machine-readable form for deterministic evaluation",
    )
    provenance: Provenance | None = None
    detector_ids: list[str] = Field(
        default_factory=list,
        description="Detectors that may evaluate this property",
    )
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
