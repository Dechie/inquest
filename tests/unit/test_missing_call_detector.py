"""Tests for the MissingCallDetector — first real verification strategy.

Three scenarios:
  A. Call graph WITHOUT reserve on the persist path → VIOLATED
  B. Call graph WITH reserve before persist → PROVEN
  C. Empty model (no graph data) → UNKNOWN
"""

from __future__ import annotations

from codeanalyzer.analysis.program_model import ProgramModelAnalysisSubstrate
from codeanalyzer.detectors.base import DetectorContext, DetectorRegistry
from codeanalyzer.detectors.missing_call import MissingCallDetector
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.entities import Entity
from codeanalyzer.domain.enums import EntityType, VerificationOutcome
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Snapshot
from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.program.graphs.call_graph import CallEdge, CallGraph
from codeanalyzer.program.in_memory import InMemoryProgramModel
from codeanalyzer.properties.catalog import RESERVE_BEFORE_PERSIST
from codeanalyzer.properties.stub import StubPropertyAPI


def _snapshot() -> Snapshot:
    return Snapshot(id="snap1", project_id="p1")


def _slice() -> LogicalSlice:
    return LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True)


def _analysis() -> AnalysisRun:
    return AnalysisRun(id="an1", slice_id="slice1", snapshot_id="snap1", status=AnalysisStatus.RUNNING)


def _make_entity(entity_id: str, snapshot: Snapshot) -> Entity:
    return Entity(id=entity_id, snapshot_id=snapshot.id, type=EntityType.METHOD, name=entity_id.split(".")[-1])


def _run_detector(model: InMemoryProgramModel) -> list:
    snapshot = _snapshot()
    slice_ = _slice()
    evidence = ProgramModelEvidenceAPI(model)
    substrate = ProgramModelAnalysisSubstrate(model)
    refiner = StubEvidenceRefiner(evidence, StubDocumentationAPI(), substrate)
    prop_api = StubPropertyAPI()
    props = prop_api.list_for_slice(snapshot, slice_)

    registry = DetectorRegistry()
    registry.register(MissingCallDetector())
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


def test_missing_call_detector_violated() -> None:
    """VIOLATED: reserve is absent; persist is reachable from checkout."""
    snapshot = _snapshot()
    # checkout → createOrder → save  (no reserve anywhere)
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="CheckoutController.checkout", callee_id="OrderService.createOrder"),
        CallEdge(caller_id="OrderService.createOrder", callee_id="OrderRepository.save"),
    ])
    entities = [
        _make_entity("CheckoutController.checkout", snapshot),
        _make_entity("OrderService.createOrder", snapshot),
        _make_entity("OrderRepository.save", snapshot),
    ]
    model = InMemoryProgramModel(snapshot, entities=entities, call_graph=call_graph)

    findings = _run_detector(model)

    ordering_findings = [f for f in findings if f.property_id == RESERVE_BEFORE_PERSIST.id]
    assert len(ordering_findings) >= 1
    outcomes = {f.verification_outcome for f in ordering_findings}
    assert VerificationOutcome.VIOLATED in outcomes


def test_missing_call_detector_proven() -> None:
    """PROVEN: reserve appears before save on the checkout path."""
    snapshot = _snapshot()
    # checkout → reserve → createOrder → save
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="CheckoutController.checkout", callee_id="InventoryService.reserve"),
        CallEdge(caller_id="InventoryService.reserve", callee_id="OrderService.createOrder"),
        CallEdge(caller_id="OrderService.createOrder", callee_id="OrderRepository.save"),
    ])
    entities = [
        _make_entity("CheckoutController.checkout", snapshot),
        _make_entity("InventoryService.reserve", snapshot),
        _make_entity("OrderService.createOrder", snapshot),
        _make_entity("OrderRepository.save", snapshot),
    ]
    model = InMemoryProgramModel(snapshot, entities=entities, call_graph=call_graph)

    findings = _run_detector(model)

    ordering_findings = [f for f in findings if f.property_id == RESERVE_BEFORE_PERSIST.id]
    assert len(ordering_findings) >= 1
    outcomes = {f.verification_outcome for f in ordering_findings}
    assert VerificationOutcome.PROVEN in outcomes


def test_missing_call_detector_unknown_empty_model() -> None:
    """UNKNOWN: empty model — no graph data for either entity."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)  # no entities, no edges

    findings = _run_detector(model)

    ordering_findings = [f for f in findings if f.property_id == RESERVE_BEFORE_PERSIST.id]
    assert len(ordering_findings) >= 1
    for f in ordering_findings:
        assert f.verification_outcome == VerificationOutcome.UNKNOWN


def test_missing_call_detector_finding_has_property_id_and_outcome() -> None:
    """Every finding from this detector must carry property_id and verification_outcome."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)
    findings = _run_detector(model)

    for finding in findings:
        if finding.detector == "possible_missing_call":
            assert finding.property_id is not None
            assert finding.verification_outcome is not None
            assert len(finding.evidence_requirements) >= 1
