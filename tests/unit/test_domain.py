"""Domain model smoke tests."""

from __future__ import annotations

from codeanalyzer.domain.enums import (
    EvidenceItemType,
    FindingSource,
    MembershipClass,
    ProvenanceKind,
    Severity,
)
from codeanalyzer.domain.evidence import EvidenceRequirement, MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice, SliceMember


def test_provenanced_fact_hypothesis_not_authoritative() -> None:
    fact = ProvenancedFact(
        statement="May violate order lifecycle",
        provenance=Provenance(
            kind=ProvenanceKind.HYPOTHESIS,
            source="llm",
        ),
    )
    assert not fact.is_authoritative_structure()


def test_program_fact_is_authoritative() -> None:
    fact = ProvenancedFact(
        statement="OrderService.createOrder calls OrderRepository.save",
        provenance=Provenance(
            kind=ProvenanceKind.PROGRAM_FACT,
            source="OrderService.php:83",
        ),
    )
    assert fact.is_authoritative_structure()


def test_logical_slice_membership_helpers() -> None:
    slice_ = LogicalSlice(
        id="slice_1",
        name="checkout",
        snapshot_id="snap_1",
        members=[
            SliceMember(entity_id="CheckoutService", membership=MembershipClass.CORE),
            SliceMember(entity_id="LoggingService", membership=MembershipClass.EXCLUDED),
            SliceMember(entity_id="NotificationService", membership=MembershipClass.RELATED),
        ],
        approved=True,
    )
    assert slice_.core_entity_ids() == ["CheckoutService"]
    assert slice_.related_entity_ids() == ["NotificationService"]
    assert set(slice_.included_entity_ids()) == {"CheckoutService", "NotificationService"}


def test_finding_and_evidence_slice() -> None:
    finding = Finding(
        id="f1",
        analysis_id="an1",
        snapshot_id="snap1",
        source=FindingSource.INTERNAL_DETECTOR,
        detector="possible_missing_call",
        type="possible_missing_call",
        severity=Severity.WARNING,
        message="InventoryService.reserve may be missing",
        evidence_requirements=[
            EvidenceRequirement(
                kind=EvidenceItemType.CALL_EDGE,
                description="call path from createOrder to save",
            )
        ],
    )
    evidence = MinimalEvidenceSlice(id="ev1", finding_id=finding.id)
    assert evidence.finding_id == "f1"
    assert finding.evidence_requirements[0].kind == EvidenceItemType.CALL_EDGE
