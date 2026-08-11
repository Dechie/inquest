"""Core domain models and enumerations."""

from codeanalyzer.domain.entities import Entity, Location, Relationship
from codeanalyzer.domain.enums import (
    EntityType,
    EvidenceItemType,
    FindingSource,
    FindingStatus,
    MembershipClass,
    ProvenanceKind,
    RelationshipType,
    Severity,
)
from codeanalyzer.domain.evidence import EvidenceItem, EvidenceRequirement, MinimalEvidenceSlice
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice, SliceMember
from codeanalyzer.domain.snapshots import AnalysisRun, Project, Snapshot

__all__ = [
    "AnalysisRun",
    "Entity",
    "EntityType",
    "EvidenceItem",
    "EvidenceItemType",
    "EvidenceRequirement",
    "Finding",
    "FindingSource",
    "FindingStatus",
    "Location",
    "LogicalSlice",
    "MembershipClass",
    "MinimalEvidenceSlice",
    "Project",
    "Provenance",
    "ProvenanceKind",
    "ProvenancedFact",
    "Relationship",
    "RelationshipType",
    "Severity",
    "SliceMember",
    "Snapshot",
]
