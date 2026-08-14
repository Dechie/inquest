"""Evidence refinement — iterative narrowing until a finding is evaluable.

Detectors identify a property/finding that requires evidence; refinement reuses
existing evidence, requests additional analysis, and produces a minimal slice.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from codeanalyzer.analysis.substrate import AnalysisSubstrate
from codeanalyzer.documentation.api import DocumentationAPI
from codeanalyzer.domain.analysis import AnalysisRequest
from codeanalyzer.domain.enums import (
    AnalysisKind,
    EvidenceItemType,
    ProvenanceKind,
    RefinementOutcome,
)
from codeanalyzer.domain.evidence import EvidenceItem, MinimalEvidenceSlice, RefinementResult
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.provenance import Provenance
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.evidence.api import EvidenceAPI


class EvidenceRefiner(ABC):
    """Builds and iteratively refines MinimalEvidenceSlice for a finding."""

    def __init__(
        self,
        evidence: EvidenceAPI,
        documentation: DocumentationAPI,
        substrate: AnalysisSubstrate,
        *,
        max_items: int = 50,
        max_rounds: int = 3,
    ) -> None:
        self.evidence = evidence
        self.documentation = documentation
        self.substrate = substrate
        self.max_items = max_items
        self.max_rounds = max_rounds

    @abstractmethod
    def refine(
        self,
        finding: Finding,
        *,
        snapshot: Snapshot,
        slice_: LogicalSlice,
        round_: int = 0,
    ) -> RefinementResult:
        """Produce or extend a minimal evidence slice for *finding*."""

    def refine_until_done(
        self,
        finding: Finding,
        *,
        snapshot: Snapshot,
        slice_: LogicalSlice,
    ) -> RefinementResult:
        """Run refinement with feedback to the analysis substrate."""
        result = self.refine(finding, snapshot=snapshot, slice_=slice_, round_=0)
        while (
            result.outcome == RefinementOutcome.NEEDS_MORE_ANALYSIS
            and result.rounds < self.max_rounds
            and result.pending_requests
        ):
            substrate_result = self.substrate.run(snapshot, slice_, result.pending_requests)
            apply_facts = getattr(self.evidence, "apply_facts", None)
            if callable(apply_facts):
                apply_facts(substrate_result.facts)
            result = self.refine(
                finding,
                snapshot=snapshot,
                slice_=slice_,
                round_=result.rounds + 1,
            )
        return result

    def empty_slice(self, finding: Finding) -> MinimalEvidenceSlice:
        return MinimalEvidenceSlice(
            id=f"evslice_{uuid.uuid4().hex[:12]}",
            finding_id=finding.id,
            property_id=finding.property_id,
        )

    def cap_items(self, slice_: MinimalEvidenceSlice) -> MinimalEvidenceSlice:
        if len(slice_.items) > self.max_items:
            slice_.items = slice_.items[: self.max_items]
            slice_.metadata["truncated"] = "true"
        return slice_


class StubEvidenceRefiner(EvidenceRefiner):
    """Scaffold refiner: maps requirements to evidence queries; requests analysis when empty."""

    _KIND_TO_ANALYSIS: dict[EvidenceItemType, AnalysisKind] = {
        EvidenceItemType.CALL_EDGE: AnalysisKind.CALL_PATH,
        EvidenceItemType.CFG_FRAGMENT: AnalysisKind.PATH_CONDITIONS,
        EvidenceItemType.DATA_FLOW_FRAGMENT: AnalysisKind.DATA_FLOW,
        EvidenceItemType.PATH_CONDITION: AnalysisKind.PATH_CONDITIONS,
        EvidenceItemType.DERIVED_FACT: AnalysisKind.REACHABILITY,
    }

    def refine(
        self,
        finding: Finding,
        *,
        snapshot: Snapshot,
        slice_: LogicalSlice,
        round_: int = 0,
    ) -> RefinementResult:
        evidence_slice = self.empty_slice(finding)
        pending: list[AnalysisRequest] = []

        for req in finding.evidence_requirements:
            evidence_slice.metadata[f"req:{req.kind.value}"] = req.description
            if req.kind == EvidenceItemType.CALL_EDGE:
                self._collect_call_edge(req, evidence_slice, pending)
            elif req.kind == EvidenceItemType.DOCUMENTATION:
                self._collect_documentation(req, finding, evidence_slice)
            elif req.kind == EvidenceItemType.EXTERNAL_DIAGNOSTIC:
                self._collect_diagnostics(req, slice_, evidence_slice)
            else:
                self._maybe_request_analysis(req, pending)

        outcome = RefinementOutcome.RESOLVED
        if pending and round_ == 0:
            outcome = RefinementOutcome.NEEDS_MORE_ANALYSIS
        elif pending:
            outcome = RefinementOutcome.UNRESOLVED
            evidence_slice.metadata["unresolved_requests"] = str(len(pending))

        return RefinementResult(
            slice=self.cap_items(evidence_slice),
            outcome=outcome,
            pending_requests=pending,
            rounds=round_,
        )

    def _collect_call_edge(
        self,
        req: object,
        evidence_slice: MinimalEvidenceSlice,
        pending: list[AnalysisRequest],
    ) -> None:
        from codeanalyzer.domain.evidence import EvidenceRequirement

        assert isinstance(req, EvidenceRequirement)
        entity_ids = req.entity_ids
        if len(entity_ids) >= 2:
            path = self.evidence.get_call_path(entity_ids[0], entity_ids[1])
            if path:
                edge = " → ".join(path)
                evidence_slice.call_edges.append(edge)
                evidence_slice.program_entities.extend(path)
                evidence_slice.items.append(
                    EvidenceItem(
                        id=f"evi_{uuid.uuid4().hex[:8]}",
                        type=EvidenceItemType.CALL_EDGE,
                        summary=edge,
                        provenance=Provenance(
                            kind=ProvenanceKind.DERIVED_FACT,
                            source="evidence_api.get_call_path",
                        ),
                        payload={"path": path},
                    )
                )
                return
            pending.append(
                AnalysisRequest(
                    kind=AnalysisKind.CALL_PATH,
                    source_id=entity_ids[0],
                    target_id=entity_ids[1],
                    scope_entity_ids=entity_ids,
                    reason=req.description,
                )
            )
        else:
            self._maybe_request_analysis(req, pending)

    def _collect_documentation(
        self,
        req: object,
        finding: Finding,
        evidence_slice: MinimalEvidenceSlice,
    ) -> None:
        from codeanalyzer.domain.evidence import EvidenceRequirement

        assert isinstance(req, EvidenceRequirement)
        docs = self.documentation.find_docs_relevant_to_finding(finding)
        for doc in docs:
            evidence_slice.documentation_ids.append(doc.id)
            evidence_slice.items.append(
                EvidenceItem(
                    id=f"evi_{uuid.uuid4().hex[:8]}",
                    type=EvidenceItemType.DOCUMENTATION,
                    summary=doc.title or doc.source,
                    provenance=Provenance(
                        kind=ProvenanceKind.DOCUMENTATION_FACT,
                        source=str(doc.location or doc.source),
                    ),
                    payload={"content": doc.content[:500]},
                )
            )

    def _collect_diagnostics(
        self,
        req: object,
        slice_: LogicalSlice,
        evidence_slice: MinimalEvidenceSlice,
    ) -> None:
        from codeanalyzer.domain.evidence import EvidenceRequirement

        assert isinstance(req, EvidenceRequirement)
        for diagnostic in self.evidence.get_external_diagnostics_for_scope(slice_):
            evidence_slice.external_diagnostic_ids.append(diagnostic.id)
            evidence_slice.items.append(
                EvidenceItem(
                    id=f"evi_{uuid.uuid4().hex[:8]}",
                    type=EvidenceItemType.EXTERNAL_DIAGNOSTIC,
                    summary=diagnostic.message,
                    provenance=Provenance(
                        kind=ProvenanceKind.EXTERNAL_ANALYZER_FACT,
                        source=diagnostic.analyzer,
                        analyzer=diagnostic.analyzer,
                        analyzer_version=diagnostic.analyzer_version,
                    ),
                    payload={"rule_id": diagnostic.rule_id or ""},
                )
            )

    def _maybe_request_analysis(
        self,
        req: object,
        pending: list[AnalysisRequest],
    ) -> None:
        from codeanalyzer.domain.evidence import EvidenceRequirement

        assert isinstance(req, EvidenceRequirement)
        kind = self._KIND_TO_ANALYSIS.get(req.kind)
        if kind is None:
            return
        entity_ids = req.entity_ids
        pending.append(
            AnalysisRequest(
                kind=kind,
                source_id=entity_ids[0] if entity_ids else None,
                target_id=entity_ids[1] if len(entity_ids) > 1 else None,
                scope_entity_ids=entity_ids,
                reason=req.description,
            )
        )
