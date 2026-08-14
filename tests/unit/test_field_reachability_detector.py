"""Tests for FieldReachabilityDetector — second real verification strategy.

Three scenarios:
  A. Data-flow graph WITH customerId → save path → PROVEN
  B. Data-flow graph WITHOUT customerId reaching save → VIOLATED
  C. Empty model (no graph data) → UNKNOWN
"""

from __future__ import annotations

from codeanalyzer.analysis.program_model import ProgramModelAnalysisSubstrate
from codeanalyzer.detectors.base import DetectorContext, DetectorRegistry
from codeanalyzer.detectors.field_reachability import FieldReachabilityDetector
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.entities import Entity
from codeanalyzer.domain.enums import EntityType, VerificationOutcome
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Snapshot
from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.program.graphs.data_flow import DataFlowEdge, DataFlowGraph
from codeanalyzer.program.in_memory import InMemoryProgramModel
from codeanalyzer.properties.catalog import REQUIRED_FIELD_REACHES_CONSUMER
from codeanalyzer.properties.stub import StubPropertyAPI


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def _snapshot() -> Snapshot:
    return Snapshot(id="snap1", project_id="p1")


def _slice() -> LogicalSlice:
    # Use a name that triggers REQUIRED_FIELD_REACHES_CONSUMER in the catalog
    return LogicalSlice(id="slice1", name="order", snapshot_id="snap1", approved=True)


def _analysis() -> AnalysisRun:
    return AnalysisRun(id="an1", slice_id="slice1", snapshot_id="snap1", status=AnalysisStatus.RUNNING)


def _make_entity(entity_id: str, snapshot: Snapshot) -> Entity:
    return Entity(
        id=entity_id,
        snapshot_id=snapshot.id,
        type=EntityType.FIELD,
        name=entity_id.split(".")[-1],
    )


def _run_detector(model: InMemoryProgramModel) -> list:
    snapshot = _snapshot()
    slice_ = _slice()
    evidence = ProgramModelEvidenceAPI(model)
    substrate = ProgramModelAnalysisSubstrate(model)
    refiner = StubEvidenceRefiner(evidence, StubDocumentationAPI(), substrate)
    prop_api = StubPropertyAPI()
    props = prop_api.list_for_slice(snapshot, slice_)

    registry = DetectorRegistry()
    registry.register(FieldReachabilityDetector())
    context = DetectorContext(
        evidence=evidence,
        documentation=StubDocumentationAPI(),
        properties=prop_api,
        snapshot=snapshot,
        slice=slice_,
        analysis=_analysis(),
        active_properties=props,
    )
    return registry.run_all(context)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_field_reachability_proven() -> None:
    """PROVEN: Order.customerId flows all the way to OrderRepository.save."""
    snapshot = _snapshot()
    data_flow = DataFlowGraph(edges=[
        DataFlowEdge(source_id="Order.customerId", target_id="CreateOrderRequest.customerId"),
        DataFlowEdge(source_id="CreateOrderRequest.customerId", target_id="OrderRepository.save"),
    ])
    model = InMemoryProgramModel(snapshot, data_flow=data_flow)

    findings = _run_detector(model)

    reachability_findings = [f for f in findings if f.property_id == REQUIRED_FIELD_REACHES_CONSUMER.id]
    assert len(reachability_findings) >= 1
    outcomes = {f.verification_outcome for f in reachability_findings}
    assert VerificationOutcome.PROVEN in outcomes


def test_field_reachability_violated() -> None:
    """VIOLATED: Order.customerId is in the graph but never reaches save."""
    snapshot = _snapshot()
    # customerId flows to a DTO but the DTO never reaches save
    data_flow = DataFlowGraph(edges=[
        DataFlowEdge(source_id="Order.customerId", target_id="LoggingService.log"),
        DataFlowEdge(source_id="Order.orderId", target_id="OrderRepository.save"),
    ])
    model = InMemoryProgramModel(snapshot, data_flow=data_flow)

    findings = _run_detector(model)

    reachability_findings = [f for f in findings if f.property_id == REQUIRED_FIELD_REACHES_CONSUMER.id]
    assert len(reachability_findings) >= 1
    outcomes = {f.verification_outcome for f in reachability_findings}
    assert VerificationOutcome.VIOLATED in outcomes


def test_field_reachability_unknown_empty_model() -> None:
    """UNKNOWN: empty data-flow graph — no evidence at all."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)  # no edges

    findings = _run_detector(model)

    reachability_findings = [f for f in findings if f.property_id == REQUIRED_FIELD_REACHES_CONSUMER.id]
    assert len(reachability_findings) >= 1
    for f in reachability_findings:
        assert f.verification_outcome == VerificationOutcome.UNKNOWN


def test_field_reachability_finding_has_required_fields() -> None:
    """Every finding must carry property_id, outcome, and evidence requirements."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)
    findings = _run_detector(model)

    for finding in findings:
        if finding.detector == "missing_field_propagation":
            assert finding.property_id is not None
            assert finding.verification_outcome is not None
            assert len(finding.evidence_requirements) >= 1
            req_kinds = {r.kind for r in finding.evidence_requirements}
            from codeanalyzer.domain.enums import EvidenceItemType
            assert EvidenceItemType.DATA_FLOW_FRAGMENT in req_kinds
