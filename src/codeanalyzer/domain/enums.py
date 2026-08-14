"""Shared enumerations for domain models."""

from __future__ import annotations

from enum import StrEnum


class ProvenanceKind(StrEnum):
    """Origin of a fact — where did it come from?

    Captures the *source* of the fact, not how firmly it is established.
    Use EpistemicStatus for certainty.
    """

    PROGRAM_FACT = "PROGRAM_FACT"                       # observed in source
    EXTERNAL_ANALYZER_FACT = "EXTERNAL_ANALYZER_FACT"   # tool diagnostic
    DERIVED_FACT = "DERIVED_FACT"                       # computed by substrate
    DOCUMENTATION_FACT = "DOCUMENTATION_FACT"           # extracted from docs
    HYPOTHESIS = "HYPOTHESIS"                           # speculative / LLM


class EpistemicStatus(StrEnum):
    """How firmly a fact is established — orthogonal to its origin.

    Provenance answers *where*; epistemic status answers *how certain*.

    OBSERVED     — directly read from source or tool output; high confidence
    DERIVED      — computed deterministically from observed facts; high confidence
    DOCUMENTED   — stated in documentation; believed but unverified in code
    INFERRED     — pattern-matched or heuristic; medium confidence
    HYPOTHESIZED — speculative, e.g. LLM suggestion; low confidence
    """

    OBSERVED = "observed"
    DERIVED = "derived"
    DOCUMENTED = "documented"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"


# Mapping from ProvenanceKind to the default EpistemicStatus it implies.
# Used to populate EpistemicStatus when not supplied explicitly.
_PROVENANCE_TO_EPISTEMIC: dict[ProvenanceKind, EpistemicStatus] = {
    ProvenanceKind.PROGRAM_FACT: EpistemicStatus.OBSERVED,
    ProvenanceKind.EXTERNAL_ANALYZER_FACT: EpistemicStatus.OBSERVED,
    ProvenanceKind.DERIVED_FACT: EpistemicStatus.DERIVED,
    ProvenanceKind.DOCUMENTATION_FACT: EpistemicStatus.DOCUMENTED,
    ProvenanceKind.HYPOTHESIS: EpistemicStatus.HYPOTHESIZED,
}


def default_epistemic_status(kind: ProvenanceKind) -> EpistemicStatus:
    """Return the conventional epistemic status for a given provenance kind."""
    return _PROVENANCE_TO_EPISTEMIC.get(kind, EpistemicStatus.INFERRED)


class EntityType(StrEnum):
    """Kinds of program entities tracked in the repository model."""

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    FIELD = "field"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    ROUTE = "route"
    SYMBOL = "symbol"
    OTHER = "other"


class RelationshipType(StrEnum):
    """Structural relationships between entities."""

    CALLS = "calls"
    IMPORTS = "imports"
    REFERENCES = "references"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    DEFINES = "defines"
    USES = "uses"
    DATA_FLOWS_TO = "data_flows_to"
    CONTAINS = "contains"
    DOCUMENTED_BY = "documented_by"
    ROUTE_HANDLES = "route_handles"


class MembershipClass(StrEnum):
    """Logical-slice membership classification."""

    CORE = "CORE"
    RELATED = "RELATED"
    EXCLUDED = "EXCLUDED"


class FindingSource(StrEnum):
    """Origin of a finding."""

    EXTERNAL_ANALYZER = "external_analyzer"
    INTERNAL_DETECTOR = "internal_detector"
    COMPOUND = "compound"  # future: detector composition


class FindingStatus(StrEnum):
    """Lifecycle status of a finding."""

    NEW = "new"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FALSE_POSITIVE = "false_positive"
    DOCUMENTATION_OUTDATED = "documentation_outdated"
    INTENDED_BEHAVIOR = "intended_behavior"
    RESOLVED = "resolved"


class Severity(StrEnum):
    """Severity ranking for diagnostics and findings."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EvidenceItemType(StrEnum):
    """Kinds of items that may appear in a minimal evidence slice."""

    PROGRAM_ENTITY = "program_entity"
    CALL_EDGE = "call_edge"
    CFG_FRAGMENT = "cfg_fragment"
    DATA_FLOW_FRAGMENT = "data_flow_fragment"
    PATH_CONDITION = "path_condition"
    EXTERNAL_DIAGNOSTIC = "external_diagnostic"
    DOCUMENTATION = "documentation"
    DERIVED_FACT = "derived_fact"
    SOURCE_SNIPPET = "source_snippet"


class PropertyKind(StrEnum):
    """Kind of correctness property / contract."""

    ORDERING = "ordering"
    INVARIANT = "invariant"
    REACHABILITY = "reachability"
    LIFECYCLE = "lifecycle"
    SCHEMA = "schema"
    STATE_TRANSITION = "state_transition"
    RESOURCE = "resource"
    API_CONTRACT = "api_contract"
    OTHER = "other"


class PropertySource(StrEnum):
    """Where a correctness property originated."""

    DOCUMENTATION = "documentation"
    DETECTOR_RULE = "detector_rule"
    FRAMEWORK = "framework"
    SCHEMA = "schema"
    USER = "user"
    LLM_EXTRACTED = "llm_extracted"


class AnalysisKind(StrEnum):
    """Deterministic analysis the substrate may run on demand."""

    REACHABILITY = "reachability"
    CALL_PATH = "call_path"
    DOMINANCE = "dominance"
    POST_DOMINANCE = "post_dominance"
    DATA_FLOW = "data_flow"
    DEF_USE = "def_use"
    PATH_CONDITIONS = "path_conditions"


class RefinementOutcome(StrEnum):
    """Result of evidence refinement for one finding."""

    RESOLVED = "resolved"
    NEEDS_MORE_ANALYSIS = "needs_more_analysis"
    UNRESOLVED = "unresolved"


class VerificationOutcome(StrEnum):
    """Mechanical result of evaluating a correctness property against evidence."""

    PROVEN = "PROVEN"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"
