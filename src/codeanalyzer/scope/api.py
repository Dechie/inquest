"""Scope API — what belongs to the logical feature?"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from codeanalyzer.domain.enums import MembershipClass
from codeanalyzer.domain.slices import LogicalSlice, SliceMember
from codeanalyzer.domain.snapshots import Snapshot


class SeedSpecification(BaseModel):
    """User input seed — not necessarily a complete slice."""

    raw: str
    kind: str | None = Field(
        default=None,
        description=(
            "directory | file | class | method | symbol | route | feature "
            "| natural_language"
        ),
    )


class CandidateSeeds(BaseModel):
    """Output of the LLM Scope Interpreter (grounded to known identifiers)."""

    intent: str
    candidate_seeds: list[str] = Field(default_factory=list)
    candidate_entities: list[str] = Field(default_factory=list)
    semantic_concepts: list[str] = Field(default_factory=list)


class ScopeProposal(BaseModel):
    """Candidate logical slice prior to human approval."""

    name: str
    description: str = ""
    members: list[SliceMember] = Field(default_factory=list)
    seed: SeedSpecification | None = None
    intent: str | None = None

    def members_by_class(self, membership: MembershipClass) -> list[SliceMember]:
        return [m for m in self.members if m.membership == membership]


class ScopeAPI(ABC):
    """Stable interface for scope resolution and slice management."""

    @abstractmethod
    def propose(
        self,
        snapshot: Snapshot,
        seed: SeedSpecification,
        *,
        project_path: str,
    ) -> ScopeProposal:
        """Run hybrid scope resolution and return a proposal for human review."""

    @abstractmethod
    def validate_proposal(self, snapshot: Snapshot, proposal: ScopeProposal) -> ScopeProposal:
        """Check structural claims against the repository representation."""

    @abstractmethod
    def approve(
        self,
        snapshot: Snapshot,
        proposal: ScopeProposal,
        *,
        edits: list[SliceMember] | None = None,
    ) -> LogicalSlice:
        """Persist an approved named logical slice (optionally after user edits)."""

    @abstractmethod
    def get_slice(self, slice_id: str) -> LogicalSlice | None: ...

    @abstractmethod
    def list_slices(self, snapshot_id: str | None = None) -> list[LogicalSlice]: ...
