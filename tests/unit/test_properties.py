"""Property and evidence refinement tests."""

from __future__ import annotations

from codeanalyzer.analysis.stub import StubAnalysisSubstrate
from codeanalyzer.documentation.stub import StubDocumentationAPI
from codeanalyzer.domain.enums import (
    EvidenceItemType,
    FindingSource,
    RefinementOutcome,
    Severity,
)
from codeanalyzer.domain.evidence import EvidenceRequirement
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.slices import LogicalSlice
from codeanalyzer.domain.snapshots import Snapshot
from codeanalyzer.evidence.refiner import StubEvidenceRefiner
from codeanalyzer.evidence.stub import StubEvidenceAPI
from codeanalyzer.properties.catalog import RESERVE_BEFORE_PERSIST
from codeanalyzer.properties.stub import StubPropertyAPI


def test_property_catalog_for_checkout_slice() -> None:
    props = StubPropertyAPI().list_for_slice(
        Snapshot(id="snap1", project_id="p1"),
        LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True),
    )
    assert any(p.id == RESERVE_BEFORE_PERSIST.id for p in props)
    assert all(p.snapshot_id == "snap1" for p in props)
    assert all(p.slice_id == "slice1" for p in props)


def test_refiner_requests_analysis_when_call_path_missing() -> None:
    finding = Finding(
        id="f1",
        analysis_id="an1",
        snapshot_id="snap1",
        source=FindingSource.INTERNAL_DETECTOR,
        property_id=RESERVE_BEFORE_PERSIST.id,
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
    refiner = StubEvidenceRefiner(
        StubEvidenceAPI(),
        StubDocumentationAPI(),
        StubAnalysisSubstrate(),
    )
    result = refiner.refine_until_done(
        finding,
        snapshot=Snapshot(id="snap1", project_id="p1"),
        slice_=LogicalSlice(id="slice1", name="checkout", snapshot_id="snap1", approved=True),
    )
    assert result.outcome in (RefinementOutcome.UNRESOLVED, RefinementOutcome.RESOLVED)
    assert result.slice.property_id == RESERVE_BEFORE_PERSIST.id
    assert "req:call_edge" in result.slice.metadata
