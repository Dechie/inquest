# Current State

**Updated:** 2026-08-14  *(FlutterAnalyzeAdapter + MypyAdapter complete; 96 tests passing)*

Operational companion to [DESIGN_SPEC.md](docs/DESIGN_SPEC.md), [DESIGN_SPEC_SUMMARY.md](docs/DESIGN_SPEC_SUMMARY.md), and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 1. Refinement judgment

The design is **architecturally strong and substantially more mature** than the original four-stage pipeline (`identify files → CFGs → BFS/DFS → LLM`). The important refinement has already happened: newer concepts were allowed to **replace, generalize, merge with, or reposition** older ones rather than accumulate beside them.

```text
Original:  code → CFG → graph algorithms → LLM

Refined:   code + analyzers → logical slice → program representation
           → deterministic analysis → evidence → properties / verification
           → minimal evidence → documentation → LLM → auditable finding
```

**Current characterization:**

> Architecture is coherent and the first two real verification strategies are operational. The next phase is a real language frontend and pressure-testing the remaining representative bug classes.

Implementation scaffolding reflects the refined architecture. The abstractions are now precise in code as well as design for the two implemented domains (call ordering, field reachability). What remains is not reinvention but **connecting real program data** and validating the remaining bug classes.

Adding correctness domains (concurrency, taint, temporal logic, …) is **less valuable** than validating current abstractions against real bug classes.

---

## 2. Summary (implementation)

Scaffolding is **re-aligned to the composable evidence-and-property architecture**. The orchestrator models the core dependency graph with one feedback loop wired:

```text
Properties (declarative)
    ↕
Detectors (verification strategies)  →  Evidence Refinement (capability)
                                              ↕ feedback
                                    Analysis Substrate (machinery)
                                              ↓
                                       Evidence API (interface)
```

**Implemented (non-stub):**

- Domain models for **CorrectnessProperty**, **AnalysisRequest**, **RefinementResult**
- **PropertyAPI** + seed catalog + **StubPropertyAPI**
- **AnalysisSubstrate** + **StubAnalysisSubstrate** (records refinement requests)
- **EvidenceRefiner** + **StubEvidenceRefiner** (iterative refinement loop)
- **DetectorContext** is property-aware; registry binds properties per detector
- **AnalysisOrchestrator** runs: properties → detectors → refine-until-done → LLM
- SQLite **`properties`** table + **PropertyStore** (schema v2 migration)
- **`EpistemicStatus`** enum — certainty dimension, separate from `ProvenanceKind`
- **`Provenance`** model — `epistemic_status` field with `@model_validator` auto-populating from `kind`; `is_high_confidence` property
- **`ProvenancedFact.is_authoritative_structure()`** — checks `epistemic_status`, excludes `HYPOTHESIZED` and `INFERRED`
- **`MissingCallDetector`** — first real verification strategy; evaluates `ORDERING` properties via call graph BFS; emits `PROVEN` / `VIOLATED` / `UNKNOWN`
- **`FieldReachabilityDetector`** — second real verification strategy; evaluates `REACHABILITY` properties via data-flow graph BFS; emits `PROVEN` / `VIOLATED` / `UNKNOWN`
- **`ProgramModelEvidenceAPI`** — real `get_data_flow()` (BFS, capped at 10 paths) and `node_in_data_flow()` helper
- **`ResourceLifecycleDetector`** — third real verification strategy; evaluates `RESOURCE` properties via call graph reachability; emits `PROVEN` / `VIOLATED` / `UNKNOWN`; VIOLATED carries `ERROR` severity
- **`InMemoryProgramModel`** — accepts injected `DataFlowGraph`; `data_flow()` returns the real graph instead of an empty one
- **`AnalysisOrchestrator.resolve_slice()`** — public convenience delegating to `scope.propose` + `scope.approve`
- **Detector registry** — `detector_id → class` map; `MissingCallDetector` and `FieldReachabilityDetector` registered; remaining IDs fall back to `StubDetector`
- **`MypyAdapter`** — real analyzer adapter; shells out to `mypy --output json --no-error-summary`; parses newline-delimited JSON; maps severity; generates UUID per diagnostic; preserves `raw_diagnostic`
- **`FlutterAnalyzeAdapter`** — real analyzer adapter; runs `flutter analyze` (no JSON mode — plain-text parsed); `_extract_issue_blocks` collapses wrapped lines; bullet-separated format `severity • message • file:line:col • rule_id`; `hint`/`info` → `Severity.INFO`, `lint` → `Severity.WARNING`

**96 tests passing.**

Prior scaffold remains (Evidence API ABC, scope pipeline, analyzer adapters, persistence stores, CLI) but is not yet backed by real program analysis.

---

## 3. Component alignment (not linear layers)

The design organizes components by **kind**, not as a strict pipeline. Conceptual dependency order ≠ runtime order.

| Component | Kind | Package | Status |
| --------- | ---- | ------- | ------ |
| Codebase & external inputs | Input sources | `analyzers/`, `repository/` | `MypyAdapter` ✓ real; `FlutterAnalyzeAdapter` ✓ real; remaining adapters stubbed |
| Logical slice | Persistent object | `scope/` | Hybrid pipeline works; expansion stubbed |
| Program representation | Data model | `program/` | Graph classes + ABCs; no language frontend |
| Analysis substrate | Computational machinery | `analysis/` | ABC + stub; no real derived facts |
| Evidence API | **Interface (central boundary)** | `evidence/api.py` | Full ABC; `ProgramModelEvidenceAPI` backend for call graph + data flow |
| Properties / contracts | **Declarative specifications** | `properties/` | API + catalog + persistence; two operative properties |
| Detectors | Verification strategies | `detectors/` | Three real strategies (`MissingCallDetector`, `FieldReachabilityDetector`, `ResourceLifecycleDetector`); rest stubbed |
| Evidence refinement | **Capability / feedback loop** | `evidence/refiner.py` | Loop wired; minimal collection |
| Minimal evidence slice | Artifact | `evidence/collector.py` | Collector exists; not finding-specific yet |
| Documentation | Dual-role input | `documentation/` | ABC + stub; intent role only in pipeline |
| LLM | Semantic interpreter | `llm/` | ABC + stub judgment |
| Findings & analysis records | Outputs / artifacts | `persistence/`, `pipeline/` | Stores write slices/analyses/properties/findings |

---

## 4. Consolidation pass (design vs code)

The architecture is sound. These **boundary precision** items are documented in the spec; code still catching up:

| Boundary | Design intent | Code today |
| -------- | ------------- | ---------- |
| **Properties** | Declarative obligations only; never query graphs or produce findings | `CorrectnessProperty` model + catalog; detectors do the work ✓ |
| **Evidence refinement** | Iterative capability; loops through substrate | Orchestrator + refiner loop wired ✓ |
| **Verification outcomes** | First-class `PROVEN` / `VIOLATED` / `UNKNOWN` | `VerificationOutcome` on `Finding`; both detectors emit real outcomes ✓ |
| **Provenance vs epistemic status** | Separate origin from certainty | Split done — `ProvenanceKind` (origin) and `EpistemicStatus` (certainty) are separate fields; `@model_validator` keeps backward compat ✓ |
| **Documentation roles** | Scope establishment + intended behavior | Scope role not yet wired in pipeline; intent associated during refinement only |
| **Detectors vs properties** | Detectors as verification strategies for properties | Property-aware context ✓; two real strategies implemented ✓ |
| **Taxonomy** | Components are different kinds of things | Docs updated; "Layer N" language avoided in new code ✓ |

---

## 5. What works (non-stub)

- **ScopeResolutionPipeline** — propose → validate → approve with injectable LLM hooks
- **CallGraph / CFG / data-flow graph** classes + BFS reachability (internal to substrate)
- **Persistence** — projects, snapshots, slices, analyses, findings, evidence, properties
- **Orchestrator** — end-to-end run loads properties, runs detectors, refines evidence, persists
- **CLI** — `init`, `status`, `scope`, `analyze`, `detectors`, `analyzers`
- **MissingCallDetector** — evaluates `ORDERING` properties; emits `PROVEN` / `VIOLATED` / `UNKNOWN`
- **FieldReachabilityDetector** — evaluates `REACHABILITY` properties; emits `PROVEN` / `VIOLATED` / `UNKNOWN`
- **ResourceLifecycleDetector** — evaluates `RESOURCE` properties; emits `PROVEN` / `VIOLATED` / `UNKNOWN`; VIOLATED at ERROR severity
- **Provenance / EpistemicStatus split** — origin and certainty are separate fields, both tested

Run verification:

```bash
pytest && mypy --strict && ruff check .
```

---

## 6. What is scaffolded (stub only)

| Component | Behavior |
| --------- | -------- |
| Language frontends / ProgramModel | ABC only; no AST or bytecode parser |
| AnalysisSubstrate | Accepts requests; returns no derived facts |
| Evidence API — field, CFG, path-condition queries | Return empty; only call graph + data flow are real |
| Property catalog | Fixed seed properties; matched heuristically by slice name |
| Remaining detectors (resource lifecycle, etc.) | Declare evidence needs; return no findings |
| Evidence refiner | Maps requirements → queries; requests analysis when data missing |
| Analyzer adapters | `MypyAdapter` ✓ (shells out to `mypy`); `FlutterAnalyzeAdapter` ✓ (plain-text parser); remaining adapters: `discover()` false, `analyze` raises |
| LLM judgment | `INSUFFICIENT_EVIDENCE` |
| Scope expansion | Passthrough stub resolver |

---

## 7. Known gaps (prioritized)

Priority follows the design: **pressure-test architecture before expanding domains**.

1. **No real language frontend** — `InMemoryProgramModel` works for tests with injected graphs; no AST parser or call-graph extractor yet. Highest-value next step.
2. **Substrate ↔ Evidence API not connected in production** — `apply_facts` + `ProgramModelEvidenceAPI` exist and are tested; orchestrator uses an empty builder by default. Wiring a real builder closes this.
3. **No analyzer execution** — external diagnostics never enter evidence; `MypyAdapter` and `FlutterAnalyzeAdapter` now real but not yet wired into the evidence pipeline.
4. **Documentation scope role unused** — pipeline uses documentation for intent only, not slice establishment.
5. **Remaining bug classes not expressed** — authentication bypass and doc contradiction are not yet modelled as properties + detectors.
6. Incremental analysis, detector composition, new analysis domains — unstarted (by design; lower priority than validating current abstractions).

---

## 8. What to do next

### Roadmap priority (from design assessment)

Representative bug classes to express **without special-case pipeline stages**:

```text
✓ Missing workflow operation (reserve before persist)     → MissingCallDetector / ORDERING
✓ Dropped field failing to reach consumer                 → FieldReachabilityDetector / REACHABILITY
✓ Resource acquired but not released on all paths         → ResourceLifecycleDetector / RESOURCE
  Authentication bypass via reachable path                → needs AuthBypassDetector / REACHABILITY
  Implementation contradicting documented invariant       → needs doc-comparison + LLM
```

Each decomposes to: **property + Evidence API queries + refinement + minimal slice**.

### Immediate

- [x] Add **VerificationOutcome** (`PROVEN` / `VIOLATED` / `UNKNOWN`) to domain + findings
- [x] Implement minimal `ProgramModel` + Evidence API backend over call graph + data flow
- [x] Bridge **analysis substrate → Evidence API** (`apply_facts` in refiner loop)
- [x] **EpistemicStatus** split from `ProvenanceKind` — origin and certainty separated
- [x] First real verification strategy — `MissingCallDetector` + `RESERVE_BEFORE_PERSIST`
- [x] Second real verification strategy — `FieldReachabilityDetector` + `REQUIRED_FIELD_REACHES_CONSUMER`
- [ ] Real language frontend for first target ecosystem (call-graph + data-flow extraction)
- [ ] Wire `ProgramModelBuilder` into orchestrator so real program data flows end-to-end

### Consolidation hygiene

- [x] Provenance (origin) and epistemic status (certainty) separated in domain models
- [ ] Wire documentation scope role into slice resolution where appropriate
- [ ] Keep pytest / mypy / ruff green
- [ ] New subsystems must go through Evidence API and Property API — no bypass

### Phase continuation (after second pressure-test passes)

- [x] `ResourceLifecycleDetector` for `RESOURCE` properties (third bug class)
- [ ] Language frontend for first target ecosystem
- [ ] One working analyzer adapter (`normalize` + persist diagnostics)
- [ ] Fourth + fifth representative bug class (auth bypass, doc contradiction)

### Doc hygiene

- Design changes → `docs/DESIGN_SPEC.md` + `docs/DESIGN_SPEC_SUMMARY.md`
- Scaffold map → `docs/ARCHITECTURE.md`
- Operational state → this file

---

## 9. Key files

```text
src/codeanalyzer/
├── analysis/
│   ├── program_model.py      # ProgramModelAnalysisSubstrate
│   └── substrate.py          # AnalysisSubstrate ABC + StubAnalysisSubstrate
├── program/
│   ├── in_memory.py          # InMemoryProgramModel (injected call graph + data flow)
│   └── graphs/
│       ├── call_graph.py     # CallGraph + BFS reachability
│       ├── cfg.py            # ControlFlowGraph
│       └── data_flow.py      # DataFlowGraph + DataFlowEdge
├── evidence/
│   ├── api.py                # EvidenceAPI ABC (central boundary)
│   ├── program_model.py      # ProgramModelEvidenceAPI — call graph + data-flow BFS
│   └── refiner.py            # StubEvidenceRefiner — iterative refinement loop
├── detectors/
│   ├── base.py               # Detector ABC, DetectorContext, DetectorRegistry
│   ├── catalog.py            # INITIAL_DETECTOR_IDS
│   ├── registry.py           # build_detectors() — real + stub mapping
│   ├── missing_call.py       # MissingCallDetector (ORDERING → PROVEN/VIOLATED/UNKNOWN)
│   ├── field_reachability.py # FieldReachabilityDetector (REACHABILITY → PROVEN/VIOLATED/UNKNOWN)
│   ├── resource_lifecycle.py # ResourceLifecycleDetector (RESOURCE → PROVEN/VIOLATED/UNKNOWN)
│   └── stubs.py              # StubDetector
├── properties/
│   ├── catalog.py            # RESERVE_BEFORE_PERSIST, REQUIRED_FIELD_REACHES_CONSUMER, …
│   └── stub.py               # StubPropertyAPI (heuristic slice matching)
├── domain/
│   ├── enums.py              # EpistemicStatus, VerificationOutcome, PropertyKind, …
│   ├── provenance.py         # Provenance (kind + epistemic_status), ProvenancedFact
│   ├── properties.py         # CorrectnessProperty
│   ├── findings.py           # Finding
│   └── analysis.py           # AnalysisRun, AnalysisRequest, RefinementResult
└── pipeline/
    └── orchestrator.py       # AnalysisOrchestrator, AnalysisResult
```

---

## 10. Design invariant

```text
Intent → Logical Slice → Program Representation
    → Analysis Substrate → Evidence API
    → Properties (declarative)
    → Verification → Outcome (PROVEN | VIOLATED | UNKNOWN)
    → Evidence Refinement → Minimal Slice
    → Documented Intent → LLM Judgment
    → Persistent Artifacts
```

Never: `source → LLM → "probably buggy"`.

**Thesis:** composable evidence-and-property engine. Refinement succeeded in design; remaining work is boundary precision in code and empirical validation against representative bugs.
