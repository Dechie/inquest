"""Shared enumerations for domain models."""

from __future__ import annotations

from enum import StrEnum


class ProvenanceKind(StrEnum):
    """Epistemic category of a fact entering the reasoning pipeline."""

    PROGRAM_FACT = "PROGRAM_FACT"
    EXTERNAL_ANALYZER_FACT = "EXTERNAL_ANALYZER_FACT"
    DERIVED_FACT = "DERIVED_FACT"
    DOCUMENTATION_FACT = "DOCUMENTATION_FACT"
    HYPOTHESIS = "HYPOTHESIS"


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
