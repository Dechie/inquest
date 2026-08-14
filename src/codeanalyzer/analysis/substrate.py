"""Deterministic analysis substrate (architecture Layer 4).

Produces derived facts for the Evidence API. BFS/DFS and similar algorithms
live here as implementation mechanisms, not architectural concepts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from codeanalyzer.domain.analysis import AnalysisRequest, SubstrateRunResult
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot


class AnalysisSubstrate(ABC):
    """Runs on-demand analyses during evidence refinement."""

    @abstractmethod
    def run(
        self,
        snapshot: Snapshot,
        slice_: LogicalSlice,
        requests: list[AnalysisRequest],
    ) -> SubstrateRunResult:
        """Satisfy *requests* and return derived facts with provenance."""

    @abstractmethod
    def supported_kinds(self) -> list[str]:
        """Analysis kinds this substrate can satisfy."""
