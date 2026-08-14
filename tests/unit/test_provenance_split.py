"""Tests for the provenance / epistemic status split."""

from __future__ import annotations

from codeanalyzer.domain.enums import EpistemicStatus, ProvenanceKind, default_epistemic_status
from codeanalyzer.domain.provenance import Provenance, ProvenancedFact


def test_provenance_kind_and_epistemic_status_are_separate_fields() -> None:
    p = Provenance(kind=ProvenanceKind.PROGRAM_FACT, source="src/foo.py:42")
    assert p.kind == ProvenanceKind.PROGRAM_FACT
    assert p.epistemic_status == EpistemicStatus.OBSERVED


def test_epistemic_status_defaults_from_kind() -> None:
    cases = {
        ProvenanceKind.PROGRAM_FACT: EpistemicStatus.OBSERVED,
        ProvenanceKind.EXTERNAL_ANALYZER_FACT: EpistemicStatus.OBSERVED,
        ProvenanceKind.DERIVED_FACT: EpistemicStatus.DERIVED,
        ProvenanceKind.DOCUMENTATION_FACT: EpistemicStatus.DOCUMENTED,
        ProvenanceKind.HYPOTHESIS: EpistemicStatus.HYPOTHESIZED,
    }
    for kind, expected in cases.items():
        p = Provenance(kind=kind, source="test")
        assert p.epistemic_status == expected, f"kind={kind}: expected {expected}, got {p.epistemic_status}"


def test_epistemic_status_can_be_set_explicitly() -> None:
    p = Provenance(
        kind=ProvenanceKind.DOCUMENTATION_FACT,
        source="docs/spec.md",
        epistemic_status=EpistemicStatus.INFERRED,
    )
    # Explicit value wins over the default derived from kind
    assert p.epistemic_status == EpistemicStatus.INFERRED
    assert p.kind == ProvenanceKind.DOCUMENTATION_FACT


def test_is_high_confidence_observed_and_derived() -> None:
    for kind in (ProvenanceKind.PROGRAM_FACT, ProvenanceKind.EXTERNAL_ANALYZER_FACT):
        p = Provenance(kind=kind, source="test")
        assert p.is_high_confidence, f"{kind} should be high confidence"


def test_is_high_confidence_false_for_uncertain() -> None:
    for kind in (ProvenanceKind.DOCUMENTATION_FACT, ProvenanceKind.HYPOTHESIS):
        p = Provenance(kind=kind, source="test")
        assert not p.is_high_confidence, f"{kind} should NOT be high confidence"


def test_provenanced_fact_authoritative_structure() -> None:
    # Observed facts are authoritative
    obs = ProvenancedFact(
        statement="A calls B",
        provenance=Provenance(kind=ProvenanceKind.PROGRAM_FACT, source="src/a.py"),
    )
    assert obs.is_authoritative_structure()

    # Hypotheses are not
    hyp = ProvenancedFact(
        statement="A might call C",
        provenance=Provenance(kind=ProvenanceKind.HYPOTHESIS, source="llm"),
    )
    assert not hyp.is_authoritative_structure()

    # Inferred facts are not (explicitly set)
    inf = ProvenancedFact(
        statement="possibly related",
        provenance=Provenance(
            kind=ProvenanceKind.DERIVED_FACT,
            source="heuristic",
            epistemic_status=EpistemicStatus.INFERRED,
        ),
    )
    assert not inf.is_authoritative_structure()


def test_default_epistemic_status_helper() -> None:
    assert default_epistemic_status(ProvenanceKind.DERIVED_FACT) == EpistemicStatus.DERIVED
    assert default_epistemic_status(ProvenanceKind.HYPOTHESIS) == EpistemicStatus.HYPOTHESIZED
