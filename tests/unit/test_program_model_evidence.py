"""Program model evidence backend and substrate bridge tests."""

from __future__ import annotations

from pathlib import Path

from codeanalyzer.analysis.program_model import ProgramModelAnalysisSubstrate
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.entities import Entity
from codeanalyzer.domain.enums import (
    EntityType,
    EvidenceItemType,
    FindingSource,
    RefinementOutcome,
    Severity,
    VerificationOutcome,
)
from codeanalyzer.domain.evidence import EvidenceRequirement
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import AnalysisRun, AnalysisStatus, Project, Snapshot
from codeanalyzer.evidence.program_model import ProgramModelEvidenceAPI
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.evidence.stub import StubEvidenceAPI
from codeanalyzer.persistence.paths import AnalysisPaths
from codeanalyzer.persistence.stores import Stores
from codeanalyzer.program.graphs.call_graph import CallEdge, CallGraph
from codeanalyzer.program.in_memory import InMemoryProgramModel
from codeanalyzer.properties.catalog import RESERVE_BEFORE_PERSIST


def _checkout_model(snapshot: Snapshot) -> InMemoryProgramModel:
    entities = [
        Entity(
            id="CheckoutController.checkout",
            snapshot_id=snapshot.id,
            type=EntityType.METHOD,
            name="checkout",
        ),
        Entity(
            id="OrderService.createOrder",
            snapshot_id=snapshot.id,
            type=EntityType.METHOD,
            name="createOrder",
        ),
        Entity(
            id="OrderRepository.save",
            snapshot_id=snapshot.id,
            type=EntityType.METHOD,
            name="save",
        ),
    ]
    call_graph = CallGraph(
        edges=[
            CallEdge(
                caller_id="CheckoutController.checkout",
                callee_id="OrderService.createOrder",
            ),
            CallEdge(
                caller_id="OrderService.createOrder",
                callee_id="OrderRepository.save",
            ),
        ]
    )
    return InMemoryProgramModel(snapshot, entities=entities, call_graph=call_graph)


def _reserve_before_persist_finding() -> Finding:
    return Finding(
        id="f1",
        analysis_id="an1",
        snapshot_id="snap1",
        source=FindingSource.INTERNAL_DETECTOR,
        property_id=RESERVE_BEFORE_PERSIST.id,
        verification_outcome=VerificationOutcome.UNKNOWN,
        detector="possible_missing_call",
        type="possible_missing_call",
        severity=Severity.WARNING,
        message="reserve may be missing on persist path",
        evidence_requirements=[
            EvidenceRequirement(
                kind=EvidenceItemType.CALL_EDGE,
                description="path from createOrder to save",
                entity_ids=["OrderService.createOrder", "OrderRepository.save"],
            )
        ],
    )


def test_finding_verification_outcome_persists(tmp_path: Path) -> None:
    paths = AnalysisPaths.for_project(tmp_path)
    stores = Stores.open(paths)
    project = Project(id="p1", path=str(tmp_path), name="demo")
    snapshot = Snapshot(id="snap1", project_id=project.id)
    slice_ = LogicalSlice(id="slice1", name="checkout", snapshot_id=snapshot.id, approved=True)
    analysis = AnalysisRun(
        id="an1",
        slice_id=slice_.id,
        snapshot_id=snapshot.id,
        status=AnalysisStatus.COMPLETED,
    )
    stores.projects.save(project)
    stores.snapshots.save(snapshot)
    stores.slices.save(slice_)
    stores.analyses.save(analysis)
    finding = _reserve_before_persist_finding()
    finding.verification_outcome = VerificationOutcome.VIOLATED
    stores.findings.save(finding)

    loaded = stores.findings.get("f1")
    assert loaded is not None
    assert loaded.verification_outcome == VerificationOutcome.VIOLATED


def test_program_model_evidence_resolves_call_path() -> None:
    snapshot = Snapshot(id="snap1", project_id="p1")
    model = _checkout_model(snapshot)
    evidence = ProgramModelEvidenceAPI(model)

    path = evidence.get_call_path("OrderService.createOrder", "OrderRepository.save")
    assert path == [
        "OrderService.createOrder",
        "OrderRepository.save",
    ]
    assert evidence.can_reach(
        "CheckoutController.checkout",
        "OrderRepository.save",
    )


def test_refiner_resolves_call_path_with_program_model() -> None:
    snapshot = Snapshot(id="snap1", project_id="p1")
    slice_ = LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True)
    model = _checkout_model(snapshot)
    evidence = ProgramModelEvidenceAPI(model)
    refiner = StubEvidenceRefiner(
        evidence,
        StubDocumentationAPI(),
        ProgramModelAnalysisSubstrate(model),
    )

    result = refiner.refine_until_done(
        _reserve_before_persist_finding(),
        snapshot=snapshot,
        slice_=slice_,
    )

    assert result.outcome == RefinementOutcome.RESOLVED
    assert result.slice.call_edges == [
        "OrderService.createOrder → OrderRepository.save",
    ]


def test_substrate_facts_bridge_into_evidence_api() -> None:
    snapshot = Snapshot(id="snap1", project_id="p1")
    slice_ = LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True)
    model = _checkout_model(snapshot)
    evidence = ProgramModelEvidenceAPI(None)
    substrate = ProgramModelAnalysisSubstrate(model)
    refiner = StubEvidenceRefiner(
        evidence,
        StubDocumentationAPI(),
        substrate,
    )

    result = refiner.refine_until_done(
        _reserve_before_persist_finding(),
        snapshot=snapshot,
        slice_=slice_,
    )

    assert result.outcome == RefinementOutcome.RESOLVED
    assert evidence.get_call_path(
        "OrderService.createOrder",
        "OrderRepository.save",
    ) == [
        "OrderService.createOrder",
        "OrderRepository.save",
    ]


def test_stub_evidence_api_ignores_substrate_facts() -> None:
    """Stub backend has no apply_facts; bridge is optional."""
    snapshot = Snapshot(id="snap1", project_id="p1")
    slice_ = LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True)
    model = _checkout_model(snapshot)
    refiner = StubEvidenceRefiner(
        StubEvidenceAPI(),
        StubDocumentationAPI(),
        ProgramModelAnalysisSubstrate(model),
    )

    result = refiner.refine_until_done(
        _reserve_before_persist_finding(),
        snapshot=snapshot,
        slice_=slice_,
    )

    assert result.outcome == RefinementOutcome.UNRESOLVED
