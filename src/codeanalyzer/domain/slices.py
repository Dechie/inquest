"""Named persistent logical slices.

A logical slice is a durable representation of a feature, module, workflow,
or subsystem. It need not correspond to a filesystem subtree.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import MembershipClass


class SliceMember(BaseModel):
    """Membership of one entity in a logical slice.

    Membership must be explainable — scores alone are not authoritative.
    """

    entity_id: str
    membership: MembershipClass
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    signals: list[str] = Field(
        default_factory=list,
        description=(
            "Membership signals, e.g. call relationship, documentation relationship"
        ),
    )


class LogicalSlice(BaseModel):
    """Named persistent logical slice.

    The same logical identity can be re-evaluated against future snapshots
    (e.g. checkout@commit-A, checkout@commit-B).
    """

    id: str
    name: str
    description: str = ""
    snapshot_id: str
    members: list[SliceMember] = Field(default_factory=list)
    inclusion_rules: list[str] = Field(default_factory=list)
    exclusion_rules: list[str] = Field(default_factory=list)
    documentation_ids: list[str] = Field(default_factory=list)
    seed_specification: str | None = Field(
        default=None,
        description="Original user seed (path, symbol, NL description, …)",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    approved: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)

    def core_entity_ids(self) -> list[str]:
        return [m.entity_id for m in self.members if m.membership == MembershipClass.CORE]

    def related_entity_ids(self) -> list[str]:
        return [m.entity_id for m in self.members if m.membership == MembershipClass.RELATED]

    def included_entity_ids(self) -> list[str]:
        return [
            m.entity_id
            for m in self.members
            if m.membership in (MembershipClass.CORE, MembershipClass.RELATED)
        ]
