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
