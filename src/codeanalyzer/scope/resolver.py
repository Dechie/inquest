"""Deterministic scope expansion and hybrid resolution pipeline.

Pipeline:
  User request
    → LLM Scope Interpreter
    → Candidate seeds/entities
    → Deterministic Scope Resolver
    → Candidate Logical Slice
    → LLM Scope Reviewer
    → Deterministic Validation
    → Human Approval
    → Named Persistent Slice
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from codeanalyzer.domain.enums import MembershipClass
from codeanalyzer.domain.slices import LogicalSlice, SliceMember
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.persistence.stores import SliceStore
from codeanalyzer.scope.api import CandidateSeeds, ScopeAPI, ScopeProposal, SeedSpecification


class DeterministicScopeResolver(ABC):
    """Expands grounded seeds using imports, call graph, references, etc."""

    @abstractmethod
    def expand(
        self,
        snapshot: Snapshot,
        seeds: CandidateSeeds,
        *,
        project_path: str,
    ) -> list[SliceMember]:
        """Expand from seeds to candidate membership with explainable reasons."""

    @abstractmethod
    def validate_structural_claims(
        self,
        snapshot: Snapshot,
        proposal: ScopeProposal,
    ) -> ScopeProposal:
        """Drop LLM-invented relationships; never let fiction enter the graph."""


class StubDeterministicScopeResolver(DeterministicScopeResolver):
    """Phase C scaffold."""

    def expand(
        self,
        snapshot: Snapshot,
        seeds: CandidateSeeds,
        *,
        project_path: str,
    ) -> list[SliceMember]:
        members: list[SliceMember] = []
        for i, seed in enumerate(seeds.candidate_seeds):
            members.append(
                SliceMember(
                    entity_id=seed,
                    membership=MembershipClass.CORE if i == 0 else MembershipClass.RELATED,
                    reasons=["seed from user/LLM interpreter (ungrounded scaffold)"],
                    signals=["semantic relationship"],
                )
            )
        for entity in seeds.candidate_entities:
            if entity not in {m.entity_id for m in members}:
                members.append(
                    SliceMember(
                        entity_id=entity,
                        membership=MembershipClass.RELATED,
                        reasons=["candidate entity from scope interpreter (scaffold)"],
                        signals=["semantic relationship"],
                    )
                )
        return members

    def validate_structural_claims(
        self,
        snapshot: Snapshot,
        proposal: ScopeProposal,
    ) -> ScopeProposal:
        # Scaffold: real validation checks claims against program model.
        return proposal


class ScopeResolutionPipeline(ScopeAPI):
    """Orchestrates hybrid scope resolution. LLM stages are injectable hooks."""

    def __init__(
        self,
        resolver: DeterministicScopeResolver | None = None,
        *,
        store: dict[str, LogicalSlice] | None = None,
        slice_store: SliceStore | None = None,
    ) -> None:
        self.resolver = resolver or StubDeterministicScopeResolver()
        self._store: dict[str, LogicalSlice] = store if store is not None else {}
        self.slice_store = slice_store

    def interpret_seed(self, seed: SeedSpecification) -> CandidateSeeds:
        """LLM Scope Interpreter hook (scaffold: passthrough).

        Production implementation must select from repository-known identifiers
        rather than inventing symbols or paths.
        """
        return CandidateSeeds(
            intent=seed.raw,
            candidate_seeds=[seed.raw] if seed.raw else [],
            candidate_entities=[],
            semantic_concepts=[],
        )

    def review_scope(
        self,
        seed: SeedSpecification,
        members: list[SliceMember],
    ) -> list[SliceMember]:
        """LLM Scope Reviewer hook (scaffold: identity).

        The LLM proposes CORE/RELATED/EXCLUDED classifications; it does not
        directly mutate the authoritative scope.
        """
        return members

    def propose(
        self,
        snapshot: Snapshot,
        seed: SeedSpecification,
        *,
        project_path: str,
    ) -> ScopeProposal:
        candidates = self.interpret_seed(seed)
        members = self.resolver.expand(snapshot, candidates, project_path=project_path)
        members = self.review_scope(seed, members)
        proposal = ScopeProposal(
            name=_slugify(seed.raw) or "unnamed",
            description=f"Proposed slice for: {seed.raw}",
            members=members,
            seed=seed,
            intent=candidates.intent,
        )
        return self.resolver.validate_structural_claims(snapshot, proposal)

    def validate_proposal(self, snapshot: Snapshot, proposal: ScopeProposal) -> ScopeProposal:
        return self.resolver.validate_structural_claims(snapshot, proposal)

    def approve(
        self,
        snapshot: Snapshot,
        proposal: ScopeProposal,
        *,
        edits: list[SliceMember] | None = None,
    ) -> LogicalSlice:
        members = edits if edits is not None else list(proposal.members)
        slice_ = LogicalSlice(
            id=f"slice_{uuid.uuid4().hex[:12]}",
            name=proposal.name,
            description=proposal.description,
            snapshot_id=snapshot.id,
            members=members,
            seed_specification=proposal.seed.raw if proposal.seed else None,
            approved=True,
        )
        self._store[slice_.id] = slice_
        if self.slice_store is not None:
            self.slice_store.save(slice_)
        return slice_

    def get_slice(self, slice_id: str) -> LogicalSlice | None:
        if self.slice_store is not None:
            return self.slice_store.get(slice_id)
        return self._store.get(slice_id)

    def list_slices(self, snapshot_id: str | None = None) -> list[LogicalSlice]:
        if self.slice_store is not None:
            return self.slice_store.list(snapshot_id=snapshot_id)
        slices = list(self._store.values())
        if snapshot_id is not None:
            slices = [s for s in slices if s.snapshot_id == snapshot_id]
        return slices


def _slugify(text: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")[:64]
