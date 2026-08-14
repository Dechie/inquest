# Codebase Correctness Analysis System (Inquest)

**Status:** Conceptually mature architectural baseline; boundary consolidation in progress

Inquest analyzes a **logically bounded part** of a codebase to answer:

> **Do declared correctness properties hold, fail, or remain unknown given available evidence?**

It combines ecosystem analyzer diagnostics, internally derived program facts, documentation (for scope and intent), and LLM semantic reasoning over a **minimal evidence slice** per verification.

This is a **composable evidence-and-property engine** — an orchestrator and evidence integrator, not an LLM code reviewer and not a replacement for mature static-analysis tooling.

## Central question

> Given a correctness property and available evidence, is it **PROVEN**, **VIOLATED**, or **UNKNOWN**?

Failure to prove is not proof of violation.

## Scalability invariant

> **Repository size must not imply proportional LLM context size.**

```text
Repository → Logical Slice → Finding → Minimal Evidence Slice → LLM
```

## Architecture at a glance

The system is a **dependency graph with feedback loops**, not a linear pipeline. Components differ by kind:

| Component | Kind |
| --------- | ---- |
| Codebase & external inputs | Input sources |
| Logical slice | Persistent object |
| Program representation | Data model |
| Analysis substrate | Computational machinery |
| Evidence API | **Interface (central boundary)** |
| Properties / contracts | **Declarative specifications** |
| Detectors | Verification strategies |
| Evidence refinement | **Capability / feedback loop** |
| Minimal evidence slice | Artifact |
| Documentation | Dual-role input (scope + intent) |
| LLM | Semantic interpreter |
| Findings & analysis records | Outputs / persistent artifacts |

```text
code + analyzers
    → logical slice (named, persisted)
    → program representation
    → analysis substrate → Evidence API
    → properties (declarative obligations)
    → detectors (verification strategies)
    → evidence refinement ↔ substrate
    → minimal evidence slice
    → documentation (scope + intent)
    → LLM semantic interpretation
    → auditable findings & analysis records
```

**Design invariant:** never collapse to `source → LLM → "probably buggy"`.

See [docs/DESIGN_SPEC_SUMMARY.md](docs/DESIGN_SPEC_SUMMARY.md) for the full architectural summary and [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md) for the complete specification. Operational status: [STATE.md](STATE.md).

## Package layout

```text
src/codeanalyzer/
├── domain/           # Models: entities, properties, findings, evidence, provenance
├── repository/       # Project + snapshot management
├── scope/            # Hybrid LLM/deterministic logical slice resolution
├── program/          # Language frontends, graphs, algorithms
├── analysis/         # Analysis substrate (deterministic fact production)
├── analyzers/        # External analyzer adapters
├── evidence/         # Evidence API + refinement + minimal slices
├── properties/       # Correctness properties / contracts
├── documentation/    # Documentation API (scope + intent roles)
├── detectors/        # Property verification strategies
├── llm/              # Scope interpretation + semantic judgment
├── persistence/      # SQLite schema, stores, .codeanalyzer/ layout
├── pipeline/         # End-to-end orchestration (with feedback loops)
└── cli.py            # Entry point
```

## Stable interfaces

| Interface | Answers |
|-----------|---------|
| **Scope API** | What belongs to the logical feature? |
| **Analyzer Adapter API** | What do ecosystem analyzers report? |
| **Evidence API** | What facts does the program establish? |
| **Property API** | What correctness obligations apply? |
| **Documentation API** | What docs relate to scope or intent? |
| **Detector / Verification API** | How is a property verified against evidence? |
| **Evidence Refinement** | What additional evidence is needed? |
| **Finding Model** | What was found, with what outcome? |
| **MinimalEvidenceSlice** | What evidence supports one verification? |
| **Analysis / Snapshot API** | Which run produced this? |
| **LLM** | What do these facts mean semantically? |

## Verification outcomes

| Outcome | Meaning |
|---------|---------|
| `PROVEN` | Evidence establishes the property holds |
| `VIOLATED` | Evidence establishes it does not hold |
| `UNKNOWN` | Insufficient or inconclusive evidence |

## Provenance & epistemic status

**Provenance** (where a fact came from) and **epistemic status** (how firmly it is established) are distinct dimensions and must not be collapsed.

| Dimension | Question |
| --------- | -------- |
| Provenance | Where did this come from? (file, tool, analysis) |
| Epistemic status | How firmly established? (observed, derived, documented, hypothesized) |

Legacy provenance kinds include `PROGRAM_FACT`, `EXTERNAL_ANALYZER_FACT`, `DERIVED_FACT`, `DOCUMENTATION_FACT`, and `HYPOTHESIS` (never authoritative over structure).

## Principles

- Reuse ecosystem analyzers; normalize diagnostics into evidence
- Deterministic facts via substrate → Evidence API; LLM never discovers structure
- Properties over suspiciousness; outcomes over vibes
- Evidence refinement is iterative; minimization is finding-specific
- Provenance and epistemic status stay separate
- `UNKNOWN` is valid and must not be silently dropped

## Storage

Analysis metadata lives under `.codeanalyzer/`:

```text
.codeanalyzer/
├── analysis.db      # SQLite — authoritative relational store
├── graphs/          # Materialized graph artifacts
├── snapshots/       # Repository snapshot metadata/artifacts
└── cache/           # Analyzer / analysis caches
```

## Development phases (roadmap)

Priority: **pressure-test representative bug classes** through the current abstractions before expanding analysis domains.

| Phase | Focus |
|-------|--------|
| **A** | Program representation (frontends, graphs, snapshots) |
| **B** | External analyzer adapters |
| **C** | Logical slice engine |
| **D** | Analysis substrate + Evidence API |
| **E** | Properties + verification strategies + outcomes |
| **F** | Evidence refinement + minimal slices |
| **G** | Documentation (intent) + LLM reasoning |
| **H** | Detector composition |
| **I** | New domains (taint, concurrency, …) after architecture validation |

Representative bug classes for architecture validation (each should express as property + evidence queries + refinement + minimal slice — no special-case stages):

- Missing workflow operation (e.g. reserve before persist)
- Dropped field failing to reach consumer
- Resource acquired but not released on all paths
- Authentication bypass via reachable path
- Implementation contradicting documented invariant

Near-term priorities:

1. Pressure-test the bug classes above through property + evidence + refinement
2. Bridge analysis substrate → Evidence API so refinement resolves on later rounds
3. First real verification strategy (`possible_missing_call` + ordering property)
4. Expand domains (taint, concurrency, …) **through** the Evidence API

## Quick start

```bash
# Install (editable)
pip install -e ".[dev]"

# CLI
codeanalyzer --help
codeanalyzer version
codeanalyzer init /path/to/project
codeanalyzer status /path/to/project

# Verify
pytest
mypy --strict src tests
ruff check src tests
```

## Non-goals (initial)

- Whole-repository LLM ingestion
- LLM discovery of graph structure or repository facts
- LLM authority over structure
- Duplicating mature local linting where ecosystem tools suffice
- Implementing every analysis domain before validating the architecture
- Treating properties as analysis mechanisms
- Treating evidence refinement as a one-pass pipeline stage
- Collapsing `UNKNOWN` into `VIOLATED`
- Collapsing provenance and epistemic status
- Treating documentation as ground truth
- Detector composition in the first implementation

## License

MIT
