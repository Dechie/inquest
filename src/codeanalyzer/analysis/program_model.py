"""Analysis substrate backed by an in-memory program model."""

from __future__ import annotations

from collections.abc import Callable

from codeanalyzer.analysis.substrate import AnalysisSubstrate
from codeanalyzer.domain.analysis import AnalysisRequest, SubstrateRunResult
from codeanalyzer.domain.enums import AnalysisKind, ProvenanceKind
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.program.algorithms.reachability import find_path
from codeanalyzer.program.graphs.call_graph import CallGraph
from codeanalyzer.program.in_memory import InMemoryProgramModel


class ProgramModelAnalysisSubstrate(AnalysisSubstrate):
    """Run call-path and reachability analyses over an in-memory call graph."""

    def __init__(self, model: InMemoryProgramModel) -> None:
        self._model = model

    def run(
        self,
        snapshot: Snapshot,
        slice_: LogicalSlice,
        requests: list[AnalysisRequest],
    ) -> SubstrateRunResult:
        facts: list[ProvenancedFact] = []
        graph = self._model.call_graph()
        for request in requests:
            if request.kind == AnalysisKind.CALL_PATH:
                facts.extend(self._call_path_facts(request, graph.callees))
            elif request.kind == AnalysisKind.REACHABILITY:
                facts.extend(self._reachability_facts(request, graph))
        return SubstrateRunResult(requests=requests, facts=facts)

    def supported_kinds(self) -> list[str]:
        return [AnalysisKind.CALL_PATH.value, AnalysisKind.REACHABILITY.value]

    def _call_path_facts(
        self,
        request: AnalysisRequest,
        neighbors: Callable[[str], list[str]],
    ) -> list[ProvenancedFact]:
        if request.source_id is None or request.target_id is None:
            return []
        path = find_path(request.source_id, request.target_id, neighbors)
        if path is None:
            return []
        return [
            ProvenancedFact(
                statement=f"call_path:{request.source_id}->{request.target_id}",
                provenance=Provenance(
                    kind=ProvenanceKind.DERIVED_FACT,
                    source="analysis_substrate.call_path",
                    snapshot_id=self._model.snapshot.id,
                ),
                entity_ids=path,
            )
        ]

    def _reachability_facts(
        self,
        request: AnalysisRequest,
        graph: CallGraph,
    ) -> list[ProvenancedFact]:
        if request.source_id is None or request.target_id is None:
            return []
        if not graph.can_reach(request.source_id, request.target_id):
            return []
        return [
            ProvenancedFact(
                statement=(
                    f"reachability:{request.source_id}->{request.target_id}"
                ),
                provenance=Provenance(
                    kind=ProvenanceKind.DERIVED_FACT,
                    source="analysis_substrate.reachability",
                    snapshot_id=self._model.snapshot.id,
                ),
                entity_ids=[request.source_id, request.target_id],
            )
        ]
