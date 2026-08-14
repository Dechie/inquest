"""Stub analysis substrate — records requests, returns no facts yet."""

from __future__ import annotations

from codeanalyzer.analysis.substrate import AnalysisSubstrate
from codeanalyzer.domain.analysis import AnalysisRequest, SubstrateRunResult
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot


class StubAnalysisSubstrate(AnalysisSubstrate):
    """Phase D scaffold: accepts refinement requests without real graph backend."""

    def __init__(self) -> None:
        self._history: list[list[AnalysisRequest]] = []

    @property
    def history(self) -> list[list[AnalysisRequest]]:
        return list(self._history)

    def run(
        self,
        snapshot: Snapshot,
        slice_: LogicalSlice,
        requests: list[AnalysisRequest],
    ) -> SubstrateRunResult:
        self._history.append(list(requests))
        return SubstrateRunResult(requests=requests, facts=[])

    def supported_kinds(self) -> list[str]:
        return []
