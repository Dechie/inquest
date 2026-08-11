# Codebase Correctness Analysis System

**Status:** Architecture baseline / initial scaffolding

Detect subtle code-correctness defects by combining:

1. **Existing ecosystem analyzers** (Flutter Analyze, ESLint, PHPStan, TypeScript, …)
2. **Deterministic program analysis** (call graph, CFG, data flow, dominance)
3. **Documentation-grounded evidence** (intent, contracts, workflows)
4. **LLM semantic reasoning** over a *minimal evidence slice*

This system is a **program-evidence integration and reasoning engine** — not an LLM code-reviewer and not a replacement for mature static-analysis tooling.

## Scalability invariant

> **Repository size must not imply proportional LLM context size.**

```text
Repository
    ↓
Logical Slice          (named feature / workflow / subsystem)
    ↓
Finding                (deterministic or external)
    ↓
Minimal Evidence Slice (smallest defensible context)
    ↓
LLM                    (semantic judgment only)
```

## Architecture at a glance

```text
User request
    → Scope resolution (LLM interpret + deterministic expand + human approve)
    → Named persistent logical slice
    → External analyzers  +  Internal graphs (AST/IR/CFG/call/data-flow)
    → Unified Evidence API
    → Detectors → Findings
    → MinimalEvidenceSlice + Documentation
    → LLM semantic judgment
```

## Package layout

```text
src/codeanalyzer/
├── domain/           # Core models: provenance, entities, findings, slices
├── repository/       # Project + snapshot management
├── scope/            # Hybrid LLM/deterministic scope resolution
├── program/          # Language frontends, graphs, algorithms
├── analyzers/        # External analyzer adapters
├── evidence/         # Evidence API + collector + minimal slices
├── documentation/    # Documentation API
├── detectors/        # Correctness detectors
├── llm/              # Semantic reasoning (scope + judgment)
├── persistence/      # SQLite schema and stores
├── pipeline/         # End-to-end orchestration
└── cli.py            # Entry point
```

## Stable interfaces

| Interface | Answers |
|-----------|---------|
| **Scope API** | What belongs to the logical feature? |
| **Analyzer Adapter API** | What does an existing ecosystem analyzer report? |
| **Evidence API** | What does the program structurally establish? |
| **Documentation API** | What is documented / intended? |
| **Detector API** | What structural anomaly is interesting? |
| **Finding Model** | What may be wrong? |
| **MinimalEvidenceSlice** | What evidence is sufficient to investigate it? |
| **LLM** | What do these facts mean semantically? |

## Provenance categories

Every important fact retains provenance:

| Kind | Meaning |
|------|---------|
| `PROGRAM_FACT` | Mechanically observed from source/graphs |
| `EXTERNAL_ANALYZER_FACT` | Produced by an established analyzer |
| `DERIVED_FACT` | Mechanically derived (reachability, dominance, …) |
| `DOCUMENTATION_FACT` | Stated intent / contract |
| `HYPOTHESIS` | Semantic interpretation (never authoritative structure) |

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

| Phase | Focus |
|-------|--------|
| **A** | Repository + program substrate (frontends, graphs, snapshots, SQLite) |
| **B** | External analyzer layer (adapters, normalization, provenance) |
| **C** | Scope engine (seeds, expansion, LLM review, persistent slices) |
| **D** | Evidence architecture (API, collector, MinimalEvidenceSlice) |
| **E** | Initial correctness detectors (missing flow/call, lifecycle, …) |
| **F** | LLM reasoning over minimal evidence |
| **G** | Detector composition |
| **H** | New analysis domains (taint, concurrency, …) |

## Quick start

```bash
# Install (editable)
pip install -e ".[dev]"

# CLI scaffold
codeanalyzer --help
codeanalyzer version

# Tests
pytest
```

## Non-goals (initial)

- Send whole repositories to an LLM
- Let the LLM invent graph structure or repository facts
- Duplicate mature local linting (unused vars, simple unreachable, …)
- Treat documentation as ground truth
- Detector composition in the first implementation

## License

MIT
