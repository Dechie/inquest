"""Tests for ResourceLifecycleDetector — third real verification strategy.

Three scenarios:
  A. Call graph WITH acquire → ... → release path → PROVEN
  B. Call graph WITH acquire but release unreachable → VIOLATED
  C. Empty model (acquire not in graph) → UNKNOWN
"""

from __future__ import annotations

from codeanalyzer.analysis.program_model import ProgramModelAnalysisSubstrate
from codeanalyzer.detectors.base import DetectorContext, DetectorRegistry
from codeanalyzer.detectors.resource_lifecycle import ResourceLifecycleDetector
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.enums import EvidenceItemType, Severity, VerificationOutcome
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Snapshot
from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.program.graphs.call_graph import CallEdge, CallGraph
from codeanalyzer.program.in_memory import InMemoryProgramModel
from codeanalyzer.properties.catalog import RESOURCE_MUST_BE_RELEASED
from codeanalyzer.properties.stub import StubPropertyAPI


def _snapshot() -> Snapshot:
    return Snapshot(id="snap1", project_id="p1")


def _slice() -> LogicalSlice:
    # "resource" in the name triggers RESOURCE_MUST_BE_RELEASED in catalog_for_slice
    return LogicalSlice(id="slice1", name="resource_manager", snapshot_id="snap1", approved=True)


def _analysis() -> AnalysisRun:
    return AnalysisRun(id="an1", slice_id="slice1", snapshot_id="snap1", status=AnalysisStatus.RUNNING)


def _run_detector(model: InMemoryProgramModel) -> list:
    snapshot = _snapshot()
    slice_ = _slice()
    evidence = ProgramModelEvidenceAPI(model)
    substrate = ProgramModelAnalysisSubstrate(model)
    refiner = StubEvidenceRefiner(evidence, StubDocumentationAPI(), substrate)
    prop_api = StubPropertyAPI()
    props = prop_api.list_for_slice(snapshot, slice_)

    registry = DetectorRegistry()
    registry.register(ResourceLifecycleDetector())
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



def test_resource_lifecycle_proven() -> None:
    """PROVEN: acquire → release path exists directly."""
    snapshot = _snapshot()
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="ServiceA.run", callee_id="ResourceManager.acquire"),
        CallEdge(caller_id="ResourceManager.acquire", callee_id="ResourceManager.release"),
    ])
    model = InMemoryProgramModel(snapshot, call_graph=call_graph)
    findings = _run_detector(model)
    resource_findings = [f for f in findings if f.property_id == RESOURCE_MUST_BE_RELEASED.id]
    assert len(resource_findings) >= 1
    assert VerificationOutcome.PROVEN in {f.verification_outcome for f in resource_findings}


def test_resource_lifecycle_proven_via_intermediate() -> None:
    """PROVEN: acquire → intermediate → release (multi-hop)."""
    snapshot = _snapshot()
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="ResourceManager.acquire", callee_id="ResourceManager.use"),
        CallEdge(caller_id="ResourceManager.use", callee_id="ResourceManager.release"),
    ])
    model = InMemoryProgramModel(snapshot, call_graph=call_graph)
    findings = _run_detector(model)
    resource_findings = [f for f in findings if f.property_id == RESOURCE_MUST_BE_RELEASED.id]
    assert VerificationOutcome.PROVEN in {f.verification_outcome for f in resource_findings}


def test_resource_lifecycle_violated_release_absent() -> None:
    """VIOLATED: acquire is in graph, release never appears anywhere."""
    snapshot = _snapshot()
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="ServiceA.run", callee_id="ResourceManager.acquire"),
        CallEdge(caller_id="ResourceManager.acquire", callee_id="ResourceManager.use"),
    ])
    model = InMemoryProgramModel(snapshot, call_graph=call_graph)
    findings = _run_detector(model)
    resource_findings = [f for f in findings if f.property_id == RESOURCE_MUST_BE_RELEASED.id]
    assert len(resource_findings) >= 1
    assert VerificationOutcome.VIOLATED in {f.verification_outcome for f in resource_findings}


def test_resource_lifecycle_violated_disconnected_graph() -> None:
    """VIOLATED: both nodes in graph but acquire cannot reach release."""
    snapshot = _snapshot()
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="ServiceA.run", callee_id="ResourceManager.acquire"),
        CallEdge(caller_id="ServiceB.run", callee_id="ResourceManager.release"),
    ])
    model = InMemoryProgramModel(snapshot, call_graph=call_graph)
    findings = _run_detector(model)
    resource_findings = [f for f in findings if f.property_id == RESOURCE_MUST_BE_RELEASED.id]
    assert VerificationOutcome.VIOLATED in {f.verification_outcome for f in resource_findings}


def test_resource_lifecycle_unknown_empty_model() -> None:
    """UNKNOWN: empty call graph — no evidence about acquire."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)
    findings = _run_detector(model)
    resource_findings = [f for f in findings if f.property_id == RESOURCE_MUST_BE_RELEASED.id]
    assert len(resource_findings) >= 1
    for f in resource_findings:
        assert f.verification_outcome == VerificationOutcome.UNKNOWN


def test_resource_lifecycle_finding_shape() -> None:
    """Every finding must carry property_id, outcome, and CALL_EDGE evidence requirement."""
    snapshot = _snapshot()
    model = InMemoryProgramModel(snapshot)
    findings = _run_detector(model)
    for finding in findings:
        if finding.detector == "resource_lifecycle_violation":
            assert finding.property_id is not None
            assert finding.verification_outcome is not None
            req_kinds = {r.kind for r in finding.evidence_requirements}
            assert EvidenceItemType.CALL_EDGE in req_kinds


def test_resource_lifecycle_violated_severity_is_error() -> None:
    """VIOLATED resource findings carry ERROR severity."""
    snapshot = _snapshot()
    call_graph = CallGraph(edges=[
        CallEdge(caller_id="ServiceA.run", callee_id="ResourceManager.acquire"),
    ])
    model = InMemoryProgramModel(snapshot, call_graph=call_graph)
    findings = _run_detector(model)
    violated = [
        f for f in findings
        if f.property_id == RESOURCE_MUST_BE_RELEASED.id
        and f.verification_outcome == VerificationOutcome.VIOLATED
    ]
    assert len(violated) >= 1
    for f in violated:
        assert f.severity == Severity.ERROR
