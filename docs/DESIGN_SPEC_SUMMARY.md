# Codebase Correctness Analysis System — Design Summary

**Status:** Conceptually mature architectural baseline; boundary consolidation in progress  
**Full specification:** [DESIGN_SPEC.md](./DESIGN_SPEC.md) · **Implementation:** [STATE.md](../STATE.md)

---

## What this system is

Inquest analyzes a **logically bounded part** of a codebase to answer:

> **Do declared correctness properties hold, fail, or remain unknown given available evidence?**

It combines ecosystem analyzer diagnostics, internally derived program facts, documentation (for scope and intent), and LLM semantic reasoning over a **minimal evidence slice** per verification.

It is an **orchestrator and evidence integrator** — not a language analyzer replacement and not an LLM code reviewer.

**Scalability invariant:** repository size must not scale LLM context proportionally.

---

## Refinement judgment

The architecture is **strong and substantially more mature** than the original `code → CFG → algorithms → LLM` pipeline. Newer concepts **replaced, generalized, merged, or repositioned** older ones rather than accumulating beside them.

```text
Original:  code → CFG → graph algorithms → LLM

Refined:   code + analyzers → logical slice → program representation
           → deterministic analysis → evidence → properties / verification
           → minimal evidence → documentation → LLM → auditable finding
```

Current state:

> **Conceptually mature, architecturally coherent — needs one consolidation pass for boundary precision, then pressure-testing against representative bug classes.**

Adding concurrency, taint, temporal logic, etc. is **less urgent** than proving representative bugs express cleanly through existing abstractions.

---

## Composable architecture (not eleven linear layers)

Earlier drafts used "eleven layers" for dependency order. That overstated linearity. Components are **different kinds of things**:

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
| Documentation | Dual-role input |
| LLM | Semantic interpreter |
| Findings & analysis records | Outputs / persistent artifacts |

Runtime is a **dependency graph** with feedback (refinement ↔ substrate, slice expansion, property refinement).

---

## What refined well

- **Logical slice** — persistent semantic boundary, not file picking
- **Program representation** — CFG/call/data-flow as representations, not stages
- **Analysis substrate** — BFS/DFS/dominance as mechanisms producing facts
- **Evidence API** — central boundary (`calls`, `reaches`, `dominates`, …)
- **Properties** — declarative obligations replace vague "bug finding"
- **Detectors** — evidence consumers, not independent analysis engines
- **Evidence refinement** — principled minimization, not "narrow graph for LLM"
- **Documentation** — promoted to correctness input (scope + intent roles)
- **LLM** — semantic interpreter, not analyzer
- **Persistence** — reproducibility, incrementality, auditability

---

## Sharpened boundaries (consolidation pass)

### Properties are declarative only

Properties state **what should hold**. They do not query graphs, run analysis, or produce findings. Verification strategies do that work.

### Evidence refinement is a capability, not a stage

Iterative feedback: gather evidence until a property is `PROVEN`, `VIOLATED`, or `UNKNOWN`. May loop through the analysis substrate. Produces **Minimal Evidence Slice** artifacts.

### Verification outcomes are first-class

```text
PROVEN    — property established to hold
VIOLATED  — property established not to hold
UNKNOWN   — insufficient or inconclusive evidence
```

**Failure to prove ≠ proof of violation.**

### Provenance ≠ epistemic status

| Dimension | Question |
| --------- | -------- |
| Provenance | Where did this come from? (file, tool, analysis) |
| Epistemic status | How firmly established? (observed, derived, documented, hypothesized) |

Do not collapse origin and certainty into one field.

### Documentation has two roles

1. **Scope establishment** — during slice resolution (what belongs to the feature?)
2. **Intended behavior** — after mechanical evidence (implementation vs intent)

### Detectors may refine further

Detectors are currently **verification strategies** for properties. They may eventually be modeled explicitly as pluggable strategies rather than co-equal fundamental abstractions.

---

## Core flow

```text
Property (declarative obligation)
    → Detector (verification strategy)
    → Evidence API queries
    → Outcome: PROVEN | VIOLATED | UNKNOWN
    → [Evidence refinement ↔ substrate if needed]
    → Minimal evidence slice
    → Documentation (intent) + LLM interpretation
    → Finding & persisted artifacts
```

**Example property:** `reserve(order) must precede persist(order)`

**Example minimal slice:**

```text
Path:      CheckoutController.checkout → OrderService.create → OrderRepository.persist
Missing:   InventoryService.reserve
Condition: paymentSucceeded == true
```

---

## Three scopes

```text
Repository  →  Logical Slice  →  Finding  →  Minimal Evidence Slice
```

Logical slices are **named and persisted**. Minimal slices are finding-specific evidence packages, not subgraph dumps.

---

## Principles (compact)

- Reuse ecosystem analyzers; normalize diagnostics into evidence
- Deterministic facts via substrate → Evidence API; LLM never discovers structure
- Properties over suspiciousness; outcomes over vibes
- Refinement is iterative; minimization is finding-specific
- Provenance and epistemic status stay separate
- `UNKNOWN` is valid and must not be silently dropped

---

## Interfaces

Scope · Analyzer Adapter · **Evidence API** · **Property API** · Documentation · Verification (Detector) · Evidence Refinement · Finding · MinimalEvidenceSlice · Analysis/Snapshot · LLM

---

## Roadmap priority

1. **Pressure-test** representative bugs (missing workflow op, dropped field, resource leak, auth bypass, doc contradiction) through property + evidence + refinement — no special-case stages
2. Bridge analysis substrate → Evidence API so refinement resolves on later rounds
3. First real verification strategy (`possible_missing_call` + ordering property)
4. Then expand domains (taint, concurrency, …) **through** Evidence API

---

## Invariant

```text
Intent → Slice → Representation → Substrate → Evidence API
    → Properties → Verification (PROVEN|VIOLATED|UNKNOWN)
    → Refinement → Minimal Slice → Intent comparison → LLM → Artifacts
```

Never: `source → LLM → "probably buggy"`.

**Thesis:** composable evidence-and-property engine. Refinement succeeded; remaining work is boundary precision and empirical validation.
