"""LLM hooks for scope interpretation and review."""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.slices import SliceMember
from codeanalyzer.scope.api import CandidateSeeds, SeedSpecification


class ScopeInterpreter(ABC):
    """Interprets user semantic intent into candidate seeds/entities.

    Must select from repository-known identifiers rather than inventing them.
    """

    @abstractmethod
    def interpret(
        self,
        seed: SeedSpecification,
        *,
        known_symbols: list[str],
        repository_structure_summary: str | None = None,
    ) -> CandidateSeeds: ...


class ScopeReviewer(ABC):
    """Classifies candidate entities as CORE / RELATED / EXCLUDED.

    The LLM proposes; it does not directly mutate the authoritative scope.
    """

    @abstractmethod
    def review(
        self,
        intent: str,
        members: list[SliceMember],
        *,
        known_relationships: list[str],
    ) -> list[SliceMember]: ...


class StubScopeInterpreter(ScopeInterpreter):
    def interpret(
        self,
        seed: SeedSpecification,
        *,
        known_symbols: list[str],
        repository_structure_summary: str | None = None,
    ) -> CandidateSeeds:
        grounded = [s for s in known_symbols if seed.raw in s or s in seed.raw]
        return CandidateSeeds(
            intent=seed.raw,
            candidate_seeds=grounded or ([seed.raw] if seed.raw else []),
            candidate_entities=[],
            semantic_concepts=[],
        )


class StubScopeReviewer(ScopeReviewer):
    def review(
        self,
        intent: str,
        members: list[SliceMember],
        *,
        known_relationships: list[str],
    ) -> list[SliceMember]:
        return members
