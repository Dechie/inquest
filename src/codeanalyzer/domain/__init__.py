"""Core domain models and enumerations."""

from codeanalyzer.domain.analysis import AnalysisRequest, SubstrateRunResult
from codeanalyzer.domain.entities import Entity, Location, Relationship
from codeanalyzer.domain.enums import (
    AnalysisKind,
    EntityType,
    EvidenceItemType,
    FindingSource,
    FindingStatus,
    MembershipClass,
    PropertyKind,
    PropertySource,
    ProvenanceKind,
    RefinementOutcome,
    RelationshipType,
    Severity,
    VerificationOutcome,
)
from codeanalyzer.domain.evidence import (
    EvidenceItem,
    EvidenceRequirement,
    MinimalEvidenceSlice,
    RefinementResult,
)
from codeanalyzer.domain.findings import Finding
from codeanalyzer.domain.properties import CorrectnessProperty
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact
from codeanalyzer.domain.slices import LogicalSlice, SliceMember
from codeanalyzer.domain.snapshots import AnalysisRun, Project, Snapshot
from codeanalyzer.domain.tooling import (
    AcquisitionMode,
    CapabilityKind,
    StructuralArtifact,
    ToolCapabilityState,
    ToolFailure,
    ToolStatus,
)

__all__ = [
    "AcquisitionMode",
    "AnalysisKind",
    "AnalysisRequest",
    "AnalysisRun",
    "CapabilityKind",
    "CorrectnessProperty",
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
    "PropertyKind",
    "PropertySource",
    "Provenance",
    "ProvenanceKind",
    "ProvenancedFact",
    "RefinementOutcome",
    "RefinementResult",
    "Relationship",
    "RelationshipType",
    "Severity",
    "SliceMember",
    "Snapshot",
    "StructuralArtifact",
    "SubstrateRunResult",
    "ToolCapabilityState",
    "ToolFailure",
    "ToolStatus",
    "VerificationOutcome",
]
