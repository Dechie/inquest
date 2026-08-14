# Codebase Correctness Analysis System

## Technical Specification & Architecture Design

**Status:** Architectural baseline — conceptually mature, boundary consolidation in progress  
**Primary objective:** Evaluate whether intended correctness properties are satisfied by the implementation.

This document supersedes the original four-stage pipeline (`identify files → CFGs → BFS/DFS/dominance → LLM`). The design has moved from a fixed analysis pipeline toward a **composable evidence-and-property architecture**.

**Related documents:** [DESIGN_SPEC_SUMMARY.md](./DESIGN_SPEC_SUMMARY.md) · [STATE.md](../STATE.md)

---

# 0. Refinement assessment

## 0.1 Overall judgment

The architecture is **strong and substantially more mature** than the original design. The important refinement has already happened: newer concepts were allowed to **replace, generalize, merge with, or reposition** older ones rather than accumulate beside them.

Current characterization:

> **Conceptually mature, architecturally coherent, but still in need of one consolidation pass to make abstractions and boundaries as precise as the underlying ideas.**

At this stage, adding more correctness domains (concurrency, temporal logic, taint, alias analysis) is **less valuable** than **pressure-testing the current architecture against representative bug classes**. If those cases can be expressed through existing abstractions without special-case components, that validates the refinement.

## 0.2 What the refinement achieved

| Original concept | Refined concept | How it changed |
| ---------------- | --------------- | -------------- |
| Identify related files | **Logical Slice** | Persistent named semantic boundary, not a temporary file list |
| CFG-centric Stage 2 | **Program Representation** | CFG, call graph, data flow, symbols, AST as representations within one substrate |
| BFS / DFS / dominance as stages | **Analysis Substrate** | Algorithms are mechanisms producing semantic facts |
| Opaque graph output | **Evidence API** | Central boundary; consumers query `calls`, `reaches`, `dominates`, `value_reaches` |
| "Find bugs" | **Properties / Contracts** | System evaluates whether declared correctness obligations hold |
| Independent analyzers called detectors | **Detectors** | Verification strategies consuming properties and evidence |
| "Narrow graph for LLM" | **Evidence Refinement** | Principled, finding-specific minimization producing **Minimal Evidence Slices** |
| Documentation as context | **Documentation** | Source of intended behavior compared against implementation evidence |
| LLM as analysis engine | **LLM** | Semantic interpreter over mechanically established evidence |
| Ephemeral analysis runs | **Persistence & named slices** | Reproducibility, incrementality, historical comparison, auditability |

The coherent result:

```text
Original:
    code → CFG → graph algorithms → LLM

Refined:
    code + analyzers
        → logical slice
        → program representation
        → deterministic analysis
        → evidence
        → properties / verification
        → minimal evidence
        → documentation
        → LLM interpretation
        → auditable finding
```

## 0.3 Refinement mechanism (ongoing)

When a missing concept is discovered, do not append it automatically. Ask:

> Does it **replace**, **generalize**, **merge with**, or **genuinely add** an existing abstraction?

Examples of successful application: Logical Slice replaced file identification; Properties replaced vague bug-finding; Evidence Refinement repositioned graph narrowing.

## 0.4 Consolidation pass (open items)

The architecture is sound; these **boundary precision** items remain:

1. **Taxonomy** — stop treating all components as "layers"; they are different kinds of things (see §2).
2. **Properties** — must remain purely **declarative correctness obligations**, never analysis mechanisms.
3. **Evidence Refinement** — model as an **iterative capability**, not a discrete pipeline stage.
4. **Documentation** — treat **scope establishment** and **intended behavior** as distinct roles.
5. **Provenance vs epistemic status** — separate "where a fact came from" from "how firmly it is established."
6. **Verification outcomes** — first-class `PROVEN`, `VIOLATED`, `UNKNOWN`; failure to prove ≠ proof of violation.
7. **Detectors vs properties** — detectors may eventually be modeled explicitly as **verification strategies** for properties rather than co-equal fundamental abstractions.

---

# 1. System objective

The system analyzes a **logically bounded subsection** of a codebase to determine whether **intended correctness properties** hold, are violated, or cannot yet be determined from available evidence.

It is an **orchestrator and evidence integrator**, not a replacement for mature ecosystem analyzers (Flutter Analyze, ESLint, PHPStan, TypeScript compiler) and not an LLM code reviewer.

It combines:

1. Existing analyzer diagnostics
2. Internally derived program facts (via analysis substrate → Evidence API)
3. Documentation and specifications (scope + intended behavior)
4. LLM semantic reasoning over a **minimal evidence slice** per verification

Central question:

> **Given a correctness property and available evidence, is the property PROVEN, VIOLATED, or UNKNOWN?**

**Scalability invariant:** repository size must not imply proportional LLM context. The LLM receives only the minimal evidence slice required to adjudicate one verification.

---

# 2. Composable architecture

## 2.1 Not a linear pipeline

Earlier drafts organized the system as "eleven layers." That was useful for establishing dependency order but **overstates linearity**. The components are fundamentally different kinds of things:

| Component | Kind | Role |
| --------- | ---- | ---- |
| Codebase & external inputs | **Input sources** | Raw material: source, structure, schemas, analyzer output |
| Logical slice | **Persistent object** | Named semantic boundary for analysis |
| Program representation | **Data model** | AST, symbols, types, graphs — reusable semantic structures |
| Analysis substrate | **Computational machinery** | Deterministic algorithms producing facts |
| Evidence API | **Interface** | Semantic query boundary over facts |
| Properties / contracts | **Declarative specifications** | Correctness obligations to evaluate |
| Detectors | **Verification strategies** | Property-specific evidence consumers (may be refined further) |
| Evidence refinement | **Capability / feedback loop** | Iteratively gather sufficient evidence |
| Minimal evidence slice | **Artifact** | Finding-specific minimized evidence package |
| Documentation | **Dual-role input** | Scope discovery + intended behavior |
| LLM | **Semantic interpreter** | Interprets mechanically established evidence |
| Findings & analysis records | **Outputs / persistent artifacts** | Auditable verification results |

**Conceptual dependency order** (what tends to depend on what — not strict runtime order):

```text
Inputs → Logical Slice → Program Representation → Analysis Substrate
    → Evidence API → Properties → Verification (detectors)
    → [Evidence Refinement ↔ Substrate] → Minimal Evidence Slice
    → Documentation (intent) → LLM → Findings & persisted artifacts
```

## 2.2 System diagram

```text
                    ┌─────────────────────┐
                    │   INPUT SOURCES     │
                    │ code · docs · tools │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   LOGICAL SLICE     │  ← persistent object
                    │   (named, stored)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ PROGRAM             │  ← data model
                    │ REPRESENTATION      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ANALYSIS SUBSTRATE  │  ← machinery
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   EVIDENCE API      │  ← interface (central boundary)
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     ┌──────────────────┐           ┌──────────────────┐
     │   PROPERTIES     │           │   DETECTORS      │
     │ (declarative)    │◄─────────►│ (verification    │
     └──────────────────┘           │  strategies)     │
                                      └────────┬─────────┘
                                               │
                    ┌──────────────────────────┴──────────────────────────┐
                    │         EVIDENCE REFINEMENT (capability)            │
                    │              ↕ feedback to substrate                │
                    └──────────────────────────┬──────────────────────────┘
                                               ▼
                    ┌─────────────────────────────────────────────────────┐
                    │         MINIMAL EVIDENCE SLICE (artifact)           │
                    └──────────────────────────┬──────────────────────────┘
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         ▼                                           ▼
              ┌──────────────────┐                        ┌──────────────────┐
              │ DOCUMENTATION    │                        │ EXT. DIAGNOSTICS │
              │ (intent role)    │                        └──────────────────┘
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │       LLM        │  ← semantic interpreter
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │ FINDINGS &       │  ← outputs / persisted artifacts
              │ ANALYSIS RECORDS │
              └──────────────────┘
```

## 2.3 Feedback loops

The architecture is a **dependency/evidence graph**, not a one-way pipeline:

```text
Verification needs more evidence
    → Analysis Substrate
    → Evidence API
    → Verification (retry)

LLM identifies ambiguous requirement
    → Property refinement
    → Evidence refinement

Analysis discovers relevant dependency
    → Slice expansion
```

---

# 3. Architectural principles

## 3.1 Reuse mature ecosystem analyzers

> Never reproduce an analysis that an established ecosystem analyzer already performs well unless needed for higher-level work.

External diagnostics normalize into evidence; they do not compete with internal verification.

## 3.2 Deterministic analysis establishes facts

Facts such as `A calls B`, `x reaches Y`, `A dominates B` are produced by the analysis substrate and exposed through the Evidence API. The LLM must not derive these from raw source.

## 3.3 Properties are declarative, not operational

A **property** states what should hold. It does **not** perform analysis, query graphs, or produce findings. Verification strategies (detectors) and the analysis substrate do that work.

## 3.4 Detectors are verification strategies, not analysis engines

Detectors declare evidence requirements, query the Evidence API, and produce **verification results** with explicit outcomes. They must not secretly rebuild analysis infrastructure.

## 3.5 Evidence refinement is iterative, not a stage

Refinement is a **capability** invoked whenever verification or LLM adjudication needs more evidence. It may loop through the analysis substrate until evidence is sufficient or outcomes remain `UNKNOWN`.

## 3.6 LLM as semantic interpreter

The LLM interprets mechanically established evidence against declared intent. It is never authoritative over structure, reachability, or graph facts.

## 3.7 Provenance and epistemic status are distinct

These answer different questions and must not be collapsed:

| Dimension | Question answered | Examples |
| --------- | ------------------- | -------- |
| **Provenance** | Where did this come from? | `OrderService.php:83`, `docs/orders.md`, `phpstan`, `reachability_analysis_v2` |
| **Epistemic status** | How firmly is it established? | `OBSERVED`, `DERIVED`, `DOCUMENTED`, `HYPOTHESIZED` |

Legacy `ProvenanceKind` values (`PROGRAM_FACT`, `DERIVED_FACT`, …) mix origin and epistemic role. New code should treat **origin** (provenance) and **status** (epistemic category) as separate fields. Migration may unify them over time without losing either dimension.

## 3.8 Verification outcomes are first-class

Every property evaluation yields one of:

```text
PROVEN     — evidence establishes the property holds
VIOLATED   — evidence establishes the property does not hold
UNKNOWN    — insufficient or inconclusive evidence
```

**Failure to prove is not proof of violation.** `UNKNOWN` must not be silently treated as `VIOLATED` or dismissed.

Lifecycle statuses for findings (`confirmed`, `false_positive`, `intended_behavior`, …) are separate from verification outcomes and describe human or LLM adjudication after mechanical verification.

---

# 4. Three distinct scopes

```text
Repository  →  Logical Slice  →  Finding  →  Minimal Evidence Slice
```

1. **Repository** — full analyzed project.
2. **Logical slice** — persistent named feature/module/workflow; may span modules; stored as a first-class object.
3. **Minimal evidence slice** — smallest defensible evidence set for one verification/finding.

---

# 5. Input sources: codebase & external analyzers

Inquest ingests:

```text
Source code · project structure · build configuration · documentation
· schemas · existing static analyzers · framework analyzers · configuration
```

Principle: existing tools are first-class inputs (`flutter analyze`, ESLint, PHPStan, TypeScript compiler, …).

### Analyzer adapter

```text
AnalyzerAdapter
├── discover() · supports() · capabilities()
├── analyze(snapshot, scope)
└── normalize(output)  →  ExternalDiagnostic
```

External diagnostics are evidence providers — they may become findings, support verification, or feed the LLM. Level-1 issues (unreachable code, unused variables) should generally be delegated to ecosystem analyzers.

---

# 6. Persistent object: logical slice

Replaces "identify related files." A slice is a **named, persisted semantic boundary**, not ephemeral preprocessing.

```text
slices/checkout/
    definition · source-snapshot · dependencies · analysis/ · findings/
```

### Scope resolution (hybrid)

```text
User seed
    → LLM Scope Interpreter (repository-known identifiers only)
    → Deterministic Resolver (imports, calls, routes, docs, conventions, …)
    → LLM Scope Review (CORE / RELATED / EXCLUDED — proposes only)
    → Deterministic Validation
    → Human Approval
    → Named Persistent Slice
```

Membership is **explainable** (reasons, not opaque scores). Slices are re-evaluable across snapshots (`checkout@commit-A/B/C`). **Slice expansion** is a feedback loop when analysis discovers new dependencies.

---

# 7. Data model: program representation

Generalizes the original CFG-centric design. CFG is **one representation** among many:

```text
AST · symbols · types · definitions · references · imports · exports
· functions · classes · call relationships · source locations
· control-flow graph · call graph · data-flow relationships
```

Future representations (state-transition, concurrency, heap/alias, effects) extend this model — do not build prematurely.

> Represent program semantics in reusable structures; don't tie the architecture to one particular graph.

Language frontends may be language-specific; verification consumes normalized semantic abstractions.

---

# 8. Computational machinery: analysis substrate

Absorbs BFS, DFS, dominance, reachability, and similar algorithms as **implementation mechanisms**, not architectural organizing principles.

Produces semantic facts:

```text
A reaches B · A dominates B · value V originates at X
· function F calls G · path P exists
```

Facts register into the Evidence API. Consumers need not know which algorithm produced them.

---

# 9. Interface: evidence API

The **central architectural boundary**. Higher-level components consume semantic evidence, not graph internals:

```text
call(A, B) · reaches(A, B) · dominates(A, B)
· definition(X) · uses(X) · value_reaches(V, X)
· path(A, B, constraints)
```

Representative operations include: entity/symbol queries, callers/callees, call paths, reachability, control-flow fragments, dominators, data-flow and provenance queries, and external diagnostics scoped to entities or slices.

Future analyzers (e.g. concurrency) expose new fact types (`happens_before(A, B)`) through this interface without architectural upheaval.

Each returned fact carries **provenance** (origin) and **epistemic status** (how established).

---

# 10. Declarative specifications: correctness properties / contracts

The central conceptual upgrade: the system evaluates **correctness obligations**, not vague suspiciousness.

A property is a **declarative specification** — what should hold — not a mechanism for performing analysis.

### Sources

Documentation · detector rules · framework semantics · schemas · user specifications · LLM-extracted requirements

### Examples

```text
reserve(order) must precede persist(order)
Every acquired resource must be released
SHIPPED implies PAID
customer.id must reach persistence
Unauthorized input must not reach privileged operation
```

### Model

```text
CorrectnessProperty
├── id
├── kind (ordering | invariant | reachability | lifecycle | schema | …)
├── statement (human-readable obligation)
├── formalization (optional — for machine evaluation)
├── source
├── scope (slice / entity set)
├── provenance (where the obligation was declared)
└── verification_outcome (PROVEN | VIOLATED | UNKNOWN) — when evaluated
```

Properties may seed from documentation but remain distinct from documentation facts and from findings.

Future kinds (preconditions, postconditions, temporal constraints, API contracts) share this abstraction.

---

# 11. Verification strategies: detectors

Detectors are **verification strategies** that evaluate properties against evidence. They may eventually be modeled as pluggable strategies bound to property kinds rather than as independent architectural peers — that relationship may refine further.

### Flow

```text
Property (declarative obligation)
    → Detector (verification strategy)
    → Evidence queries via Evidence API
    → Verification result (PROVEN | VIOLATED | UNKNOWN)
    → Finding candidate (when VIOLATED or inconclusive)
```

### Design rules

1. Declare required evidence kinds.
2. Query only through Evidence API.
3. Produce mechanically grounded results with reconstructable provenance.
4. Never perform hidden large-scale independent analysis.
5. Distinguish `UNKNOWN` from `VIOLATED`.

Detectors must **not**: construct LLM prompts, fetch arbitrary files, own graph models, or serialize evidence for the LLM.

### Initial verification focus

Missing call/argument/field flow, use-before-def, null flow, resource lifecycle, workflow deviation, call/data-flow anomalies — deliberately beyond local linting delegated to external analyzers.

### External vs internal findings

Common finding model; external analyzer output and internal verification both participate. Finding lifecycle statuses (`new`, `confirmed`, `rejected`, `false_positive`, …) are adjudication states distinct from `PROVEN`/`VIOLATED`/`UNKNOWN`.

---

# 12. Capability: evidence refinement

**Not a discrete pipeline stage.** An iterative capability invoked when verification or adjudication needs more evidence.

> Detectors (or the LLM) identify what must be established; refinement gathers evidence until the property is PROVEN, VIOLATED, or remains UNKNOWN.

Refinement may:

```text
reuse existing evidence
request additional analysis (feedback to substrate)
expand paths · trace backward/forward
add conditions · definitions · documentation
remove irrelevant material
```

### Artifact: minimal evidence slice

The **output** of successful refinement — a first-class persisted artifact:

```text
MinimalEvidenceSlice
├── finding / property reference
├── verification_outcome
├── program entities · call edges · CFG/data-flow fragments
├── external diagnostics · relevant conditions
├── documentation references
├── provenance + epistemic metadata
└── (not the full logical slice)
```

> Minimum sufficient evidence, not maximum available context.

**Example:**

```text
Property:   reserve(order) must precede persist(order)
Outcome:    VIOLATED (mechanical) / UNKNOWN (pending LLM on intent)

Minimal slice:
    CheckoutController.checkout → OrderService.create → OrderRepository.persist
    Missing: InventoryService.reserve
    Condition: paymentSucceeded == true
```

---

# 13. Documentation (dual role)

Documentation is not only post-hoc intent comparison. It has **two distinct architectural roles**:

| Role | When used | Purpose |
| ---- | --------- | ------- |
| **Scope establishment** | Logical slice resolution | Identify what belongs to a feature; associate entities with documented workflows |
| **Intended behavior** | After mechanical evidence | Compare implementation evidence against declared requirements |

Both roles feed the system, but at different points. Scope-related documentation influences slice membership and property discovery; intent-related documentation enters verification and LLM adjudication **after** mechanical evidence is assembled.

Documentation is intent evidence, not ground truth — may be incomplete, stale, or wrong.

### Documentation API

Operations for entity docs, requirements, invariants, workflows, constraints, batch entity lookup, and finding-relevant doc retrieval — scoped to logical slice and finding-implicated entities.

Documentation may **seed properties** but properties remain first-class declarative objects once extracted.

---

# 14. LLM semantic reasoning

Invoked **after** mechanical verification and evidence refinement. Input:

```text
Logical slice · property · verification outcome · minimal evidence slice
· detector result · relevant documentation (intent role)
· analyzer diagnostics · source excerpts · provenance/epistemic metadata
```

The LLM interprets:

* Does a mechanical discrepancy constitute a real violation of documented behavior?
* Is documentation applicable to this path?
* Is this an intentional exception?
* How should the finding be explained?

It does **not** discover graph structure or override deterministic facts. It may upgrade or downgrade confidence but should preserve `UNKNOWN` where evidence is genuinely inconclusive.

---

# 15. Outputs & persistent artifacts

Everything worth retaining becomes a durable analysis object:

```text
Analysis Record
├── slice · snapshot
├── analyzer results · program representations · evidence cache
├── properties (declared obligations)
├── verification executions · verification outcomes
├── minimal evidence slices
├── documentation references
├── LLM judgments
└── findings (with full provenance chain)
```

Findings link: property evaluated, verification outcome, epistemic status of supporting facts, detector/strategy used, counterexample evidence, documentation, LLM interpretation.

### Storage

SQLite — authoritative metadata and relationships. Filesystem — large graph artifacts under `.codeanalyzer/`. Every analysis binds to commit hash; analyzer versions retained. Incremental invalidation: changed entities → affected slices → recompute.

Two optimizations: **scope** (what code defines a feature?) vs **evidence minimization** (what evidence evaluates one finding?).

---

# 16. End-to-end operational flow

Typical flow (feedback loops may repeat steps):

```text
 1. User describes logical subject
 2. Scope resolution (docs assist scope role) → persisted slice
 3. Program representation built for slice
 4. External analyzers + analysis substrate run in parallel
 5. Facts available via Evidence API
 6. Properties loaded / derived (docs may seed properties)
 7. Detectors verify properties → PROVEN / VIOLATED / UNKNOWN
 8. Evidence refinement produces minimal slices (loops to substrate if needed)
 9. Documentation (intent role) associated; implementation vs intent prepared
10. LLM semantic interpretation (where needed)
11. Findings and analysis records persisted
12. Developer confirms / rejects / resolves
```

---

# 17. Stable interfaces

| Interface | Kind | Question |
| --------- | ---- | -------- |
| Scope API | Interface | What belongs to the logical feature? |
| Analyzer Adapter API | Input integration | What do ecosystem analyzers report? |
| Evidence API | Interface | What facts does the program establish? |
| Property API | Declarative spec access | What correctness obligations apply? |
| Documentation API | Input integration | What docs relate to scope or intent? |
| Detector / Verification API | Strategy | How is a property verified against evidence? |
| Evidence Refinement API | Capability | What additional evidence is needed? |
| Finding Model | Output | What was found, with what outcome? |
| MinimalEvidenceSlice | Artifact | What evidence supports one verification? |
| Analysis / Snapshot API | Persistence | Which run produced this? |
| LLM Semantic Layer | Interpreter | What do these facts mean? |

---

# 18. Non-goals (initial)

* Whole-repo LLM ingestion
* LLM discovery of graph structure
* LLM authority over structure
* Duplicating mature analyzers
* Implementing every analysis domain before validating the architecture
* Treating properties as analysis mechanisms
* Treating evidence refinement as a one-pass pipeline stage
* Collapsing `UNKNOWN` into `VIOLATED`
* Collapsing provenance and epistemic status
* Treating documentation as ground truth
* Detector composition in v1

---

# 19. Implementation roadmap

Priority: **validate architecture against representative bug classes** before expanding domains.

| Phase | Focus |
| ----- | ----- |
| A | Program representation (frontends, AST, graphs, snapshots) |
| B | External analyzer adapters |
| C | Logical slice engine (documentation scope role) |
| D | Analysis substrate + Evidence API (provenance/epistemic separation) |
| E | Properties + verification strategies (detectors) + `PROVEN`/`VIOLATED`/`UNKNOWN` |
| F | Evidence refinement capability + minimal slices |
| G | Documentation intent role + LLM semantic reasoning |
| H | Detector composition |
| I | New domains **only after** architecture validation via representative bugs |

Representative bug classes for architecture pressure-testing:

```text
Missing workflow operation (reserve before persist)
Dropped field failing to reach consumer
Resource acquired but not released on all paths
Authentication bypass via reachable path
Implementation contradicting documented invariant
External diagnostic correlated with internal data-flow break
```

Each should express as: property + evidence queries + refinement + minimal slice — without special-case pipeline stages.

---

# 20. Design invariant

Preserve the provenance-bearing verification chain:

```text
Intent → Logical Slice → Program Representation
    → Analysis Substrate → Evidence API
    → Properties (declarative)
    → Verification → Outcome (PROVEN | VIOLATED | UNKNOWN)
    → Evidence Refinement → Minimal Slice
    → Documented Intent → LLM Judgment
    → Persistent Artifacts
```

Never collapse to:

```text
source code → LLM → "probably buggy"
```

---

# 21. Architectural thesis

Inquest is a **composable program-evidence integration and reasoning engine**.

| Distinction | Content |
| ----------- | ------- |
| Central correctness question | Do declared properties hold, fail, or remain unknown? |
| Central scalability mechanism | Repository → slice → finding → minimal evidence slice → LLM |
| Central integration principle | Reuse analyzers; normalize to evidence; verify properties; reason semantically |
| Central maturity criterion | Representative bug classes expressible without special-case components |

Escalating sophistication without whole-repo LLM context:

```text
Local analyzer diagnostic
    → Cross-file graph fact
    → Property evaluation (VIOLATED / UNKNOWN)
    → Minimal evidence slice
    → Implementation-vs-documentation judgment
    → Compound, auditable correctness finding
```

The refinement succeeded. The remaining work is **boundary precision and empirical validation**, not architectural reinvention.
