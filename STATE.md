# Current State

**Updated:** 2026-08-14

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

> Conceptually mature, architecturally coherent — still in need of one consolidation pass for boundary precision, then pressure-testing against representative bug classes.

Implementation scaffolding reflects the refined architecture. What remains is not reinvention but **making abstractions as precise in code as they are in the design**, then proving representative bugs express cleanly through them.

At this stage, adding correctness domains (concurrency, taint, temporal logic, …) is **less valuable** than validating the current abstractions against real bug classes.

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

**Implemented now** (stub-level for heavy analysis work):

- Domain models for **CorrectnessProperty**, **AnalysisRequest**, **RefinementResult**
- **PropertyAPI** + seed catalog + **StubPropertyAPI**
- **AnalysisSubstrate** + **StubAnalysisSubstrate** (records refinement requests)
- **EvidenceRefiner** + **StubEvidenceRefiner** (iterative refinement loop)
- **DetectorContext** is property-aware; registry binds properties per detector
- **AnalysisOrchestrator** runs: properties → detectors → refine-until-done → LLM
- SQLite **`properties`** table + **PropertyStore** (schema v2 migration)

Prior scaffold remains (domain models, Evidence API ABC, scope pipeline, analyzer adapters, persistence stores, CLI) but is not yet backed by real program analysis.

---

## 3. Component alignment (not linear layers)

The design organizes components by **kind**, not as a strict pipeline. Conceptual dependency order ≠ runtime order.

| Component | Kind | Package | Status |
| --------- | ---- | ------- | ------ |
| Codebase & external inputs | Input sources | `analyzers/`, `repository/` | Adapters stubbed; no execution |
| Logical slice | Persistent object | `scope/` | Hybrid pipeline works; expansion stubbed |
| Program representation | Data model | `program/` | Graph classes + ABCs; no frontend |
| Analysis substrate | Computational machinery | `analysis/` | ABC + stub; no real facts |
| Evidence API | **Interface (central boundary)** | `evidence/api.py` | Full ABC; stub backend |
| Properties / contracts | **Declarative specifications** | `properties/` | API + catalog + persistence |
| Detectors | Verification strategies | `detectors/` | Property-aware; no real evaluations yet |
| Evidence refinement | **Capability / feedback loop** | `evidence/refiner.py` | Loop wired; minimal collection |
| Minimal evidence slice | Artifact | `evidence/collector.py` | Collector exists; not finding-specific yet |
| Documentation | Dual-role input | `documentation/` | ABC + stub; intent role only in pipeline |
| LLM | Semantic interpreter | `llm/` | ABC + stub judgment |
| Findings & analysis records | Outputs / artifacts | `persistence/`, `pipeline/` | Stores write slices/analyses/properties |

**What refined well in design (now reflected in code structure):**

- Logical slice as persistent semantic boundary, not file picking
- Program representation as data model, not a pipeline stage
- Analysis substrate absorbing algorithms as fact-producing machinery
- Evidence API as the central query boundary
- Properties replacing vague "bug finding"
- Detectors as evidence consumers, not independent analysis engines
- Evidence refinement as iterative capability, not one-pass graph narrowing
- Documentation promoted to correctness input (partially wired)
- LLM repositioned as semantic interpreter
- Persistence and named slices as first-class artifacts

---

## 4. Consolidation pass (design vs code)

The architecture is sound. These **boundary precision** items are documented in the spec; code still catching up:

| Boundary | Design intent | Code today |
| -------- | ------------- | ---------- |
| **Properties** | Declarative obligations only; never query graphs or produce findings | `CorrectnessProperty` model + catalog; detectors do the work ✓ |
| **Evidence refinement** | Iterative capability; loops through substrate | Orchestrator + refiner loop wired ✓ |
| **Verification outcomes** | First-class `PROVEN` / `VIOLATED` / `UNKNOWN` | `VerificationOutcome` on `Finding`; persisted ✓ |
| **Provenance vs epistemic status** | Separate origin from certainty | `ProvenanceKind` conflates both (legacy); needs split |
| **Documentation roles** | Scope establishment + intended behavior | Scope role not wired in pipeline; intent associated during refinement only |
| **Detectors vs properties** | Detectors as verification strategies for properties | Property-aware context ✓; explicit strategy model deferred |
| **Taxonomy** | Components are different kinds of things | Docs updated; avoid "Layer N" in new code/comments |

---

## 5. What works (non-stub)

- **ScopeResolutionPipeline** — propose → validate → approve with injectable LLM hooks
- **CallGraph / CFG / data-flow graph** classes + BFS reachability (internal to substrate)
- **Persistence** — projects, snapshots, slices, analyses, findings, evidence, properties
- **Orchestrator** — end-to-end run loads properties, runs detectors, refines evidence, persists
- **CLI** — `init`, `status`, `scope`, `analyze`, `detectors`, `analyzers`

Run verification:

```bash
pytest && mypy --strict && ruff check .
```

---

## 6. What is scaffolded (stub only)

| Component | Behavior |
| --------- | -------- |
| Language frontends / ProgramModel | ABC only |
| AnalysisSubstrate | Accepts requests; returns no derived facts |
| Evidence API backend | All queries empty |
| Property catalog | Fixed seed properties; heuristic by slice name |
| Detectors | Declare evidence needs; return no findings |
| Evidence refiner | Maps requirements → queries; requests analysis when data missing |
| Analyzer adapters | `discover()` false; `analyze` raises |
| LLM judgment | `INSUFFICIENT_EVIDENCE` |
| Scope expansion | Passthrough stub resolver |
| Verification outcomes | Enum + finding field; detectors don't emit yet |

---

## 7. Known gaps (prioritized)

Priority follows the design: **pressure-test architecture before expanding domains**.

1. **Substrate ↔ Evidence API not connected** — bridge wired via `apply_facts` + `ProgramModelEvidenceAPI`; orchestrator still uses stub backend by default.
2. **No real program representation** — `InMemoryProgramModel` + call-graph evidence backend exist for tests; no language frontend yet.
3. **No real verification strategies** — property binding exists but no detector evaluates properties → `PROVEN`/`VIOLATED`/`UNKNOWN`.
4. **No analyzer execution** — external diagnostics never enter evidence.
5. **Verification outcomes not first-class** — enum + finding field done; detectors do not emit outcomes yet.
6. **Provenance / epistemic status not separated** — legacy `ProvenanceKind` mixes origin and certainty.
7. **Documentation scope role unused** — pipeline uses documentation for intent only, not slice establishment.
8. Incremental analysis, detector composition, new analysis domains — unstarted (by design).

---

## 8. What to do next

### Roadmap priority (from design assessment)

Representative bug classes to express **without special-case pipeline stages**:

```text
Missing workflow operation (reserve before persist)
Dropped field failing to reach consumer
Resource acquired but not released on all paths
Authentication bypass via reachable path
Implementation contradicting documented invariant
```

Each should decompose to: **property + Evidence API queries + refinement + minimal slice**.

### Immediate

- [x] Add **VerificationOutcome** (`PROVEN` / `VIOLATED` / `UNKNOWN`) to domain + findings
- [x] Implement minimal `ProgramModel` + Evidence API backend over call graph
- [x] Bridge **analysis substrate → Evidence API** (`apply_facts` in refiner loop)
- [ ] Wire bridge into orchestrator with real program data

### First real verification strategy

- [ ] Implement `possible_missing_call` against `RESERVE_BEFORE_PERSIST` using only Evidence API
- [ ] Finding carries `property_id` + verification outcome; refiner builds minimal slice from call path + doc invariant
- [ ] Use this as the first architecture pressure-test (missing workflow operation)

### Consolidation hygiene

- [ ] Begin separating provenance (origin) from epistemic status in domain models
- [ ] Wire documentation scope role into slice resolution where appropriate
- [ ] Keep pytest / mypy / ruff green
- [ ] New subsystems must go through Evidence API and Property API — no bypass

### Phase continuation (after first pressure-test passes)

- [ ] Language frontend for first target ecosystem
- [ ] One working analyzer adapter (`normalize` + persist diagnostics)
- [ ] Second representative bug class through same abstractions

### Doc hygiene

- Design changes → `docs/DESIGN_SPEC.md` + `docs/DESIGN_SPEC_SUMMARY.md`
- Scaffold map → `docs/ARCHITECTURE.md`
- Operational state → this file

---

## 9. Key files

```text
src/codeanalyzer/
├── analysis/
│   ├── program_model.py   # Substrate over in-memory call graph
│   └── substrate.py
├── program/
│   └── in_memory.py       # Minimal ProgramModel implementation
├── evidence/
│   ├── program_model.py   # Call-graph Evidence API + apply_facts
│   └── refiner.py         # Applies substrate facts between rounds
├── properties/
├── domain/
│   ├── properties.py
│   └── analysis.py
├── detectors/base.py
└── pipeline/orchestrator.py
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
