# Codebase Correctness Analysis System

## Technical Specification & Architecture Design

**Status:** Architecture baseline
**Primary objective:** Detect subtle code-correctness defects by combining existing ecosystem analyzers, deterministic program analysis, documentation-grounded evidence, and LLM semantic reasoning.

---

# 1. System Objective

The system analyzes a logically defined subsection of a codebase rather than indiscriminately analyzing the entire repository.

Its purpose is to detect defects ranging from conventional static-analysis errors to subtle cross-function, cross-file, data-flow, call-flow, and implementation-vs-intent discrepancies.

The system does **not** attempt to replace established analyzers such as Flutter Analyze, ESLint, PHPStan, or the TypeScript compiler. Instead, it integrates their output into a unified evidence and reasoning architecture while implementing analyses that require broader program context.

The system combines four classes of information:

1. **Existing analyzer diagnostics**
2. **Internally derived program facts**
3. **Documentation/specification describing intended behavior**
4. **LLM semantic reasoning over a minimal evidence slice**

The fundamental pipeline is:

```text
Repository
    │
    ▼
Scope Resolution
    │
    ▼
Named Logical Slice
    │
    ├───────────────────────┐
    ▼                       ▼
Existing Analyzers      Internal Analysis
    │                       │
Flutter Analyze          AST / IR
ESLint                   Call Graph
PHPStan                  CFG
TypeScript               Data Flow
...                      Dominance
    │                       │
    └───────────┬───────────┘
                ▼
        Unified Evidence
                │
                ▼
           Detectors
                │
                ▼
             Finding
                │
                ▼
      Minimal Evidence Slice
                │
          ┌─────┴─────┐
          ▼           ▼
     Program Data   Documentation
          └─────┬─────┘
                ▼
               LLM
                │
                ▼
       Semantic Judgment
```

The critical scalability invariant is:

> **Repository size must not imply proportional LLM context size.**

The internal analysis engine may operate on large graphs, but the LLM receives only the smallest evidence slice necessary to evaluate a particular finding.

---

# 2. Architectural Principles

## 2.1 Existing analyzers are first-class analysis providers

Where a mature ecosystem analyzer already performs an analysis reliably, the system should consume it rather than reimplementing it.

Examples:

```text
Flutter Analyze
ESLint
PHPStan
TypeScript compiler
language-server diagnostics
framework-specific analyzers
```

The system should therefore be an **analysis orchestrator and evidence integrator**, not an attempt to recreate every language-specific static analyzer.

---

## 2.2 Internal analysis targets higher-order questions

The custom analysis engine focuses primarily on questions that require broader context, such as:

* cross-function data flow;
* cross-file call relationships;
* workflow correctness;
* path-sensitive behavior;
* dominance relationships;
* missing operations;
* missing argument/field propagation;
* unexpected call paths;
* implementation-vs-documentation discrepancies.

---

## 2.3 Deterministic analysis establishes program facts

Deterministic analysis establishes mechanically defensible facts.

Examples:

```text
A calls B
x reaches Y
x does not reach Y
A can reach B
A dominates B
B post-dominates A
there exists a path without operation X
field f is produced at A and consumed at B
```

The LLM should not be responsible for discovering such facts from raw source when deterministic analysis can establish them.

---

## 2.4 LLMs perform semantic interpretation

LLMs are used where semantic interpretation is difficult to encode deterministically:

* interpreting a user's requested feature;
* identifying candidate logical components;
* reviewing proposed scope;
* comparing implementation against documented intent;
* correlating multiple mechanically established facts;
* evaluating whether an implementation/intent discrepancy is likely a defect;
* explaining findings;
* proposing remediation.

The LLM is never the authoritative source for repository structure or graph facts.

---

## 2.5 Documentation is a first-class analysis input

Documentation represents intended behavior and constraints.

Potential sources include:

* README files;
* architecture documents;
* requirements;
* API specifications;
* module documentation;
* function/class documentation;
* doc comments;
* workflow descriptions;
* developer-defined contracts;
* design documents.

Documentation is evidence of intent, not automatically ground truth. It may be incomplete, stale, or incorrect.

---

## 2.6 Provenance is mandatory

Every important fact entering the reasoning pipeline must retain provenance.

At minimum:

```text
PROGRAM_FACT
EXTERNAL_ANALYZER_FACT
DERIVED_FACT
DOCUMENTATION_FACT
HYPOTHESIS
```

Example:

```text
PROGRAM_FACT
OrderService.createOrder calls OrderRepository.save
source: OrderService.php:83
```

```text
EXTERNAL_ANALYZER_FACT
flutter_analyze: undefined_method
source: checkout.dart:142
analyzer_version: ...
```

```text
DOCUMENTATION_FACT
"Inventory must be reserved before persistence."
source: docs/orders.md
```

```text
HYPOTHESIS
The implementation may violate the documented order lifecycle.
```

The system must preserve the distinction between observation, derivation, external diagnostics, and semantic interpretation.

---

# 3. Three Distinct Scopes

The architecture explicitly distinguishes three levels.

## 3.1 Repository Scope

The complete analyzed project/repository.

```text
Repository
```

---

## 3.2 Logical Slice

A persistent, named representation of a logical feature, module, workflow, or subsystem.

Example:

```text
checkout
├── CheckoutController
├── CheckoutService
├── CartService
├── InventoryService
├── PaymentService
├── OrderService
└── OrderRepository
```

A logical slice need not correspond to a filesystem subtree.

It may span multiple modules, directories, services, shared components, repositories, and infrastructure.

---

## 3.3 Minimal Evidence Slice

The smallest subset of the logical slice sufficient to establish or evaluate one particular finding.

Example:

```text
CheckoutService.checkout
        │
        ▼
InventoryService.reserve
        │
        ▼
OrderRepository.save

+ relevant data-flow
+ relevant conditions
+ relevant documentation
```

The fundamental hierarchy is:

```text
Repository
    ↓
Logical Slice
    ↓
Finding
    ↓
Minimal Evidence Slice
```

These must remain distinct abstractions.

---

# 4. Scope Resolution

## 4.1 User input is a seed, not necessarily a slice

The user may specify:

* directory;
* file;
* class;
* method/function;
* symbol;
* multiple symbols;
* API endpoint;
* feature name;
* natural-language description.

Examples:

```text
features/orders/
```

```text
OrderService.createOrder()
```

```text
POST /orders
```

```text
"Analyze the checkout workflow."
```

Each becomes an initial seed specification.

---

# 5. Hybrid LLM/Deterministic Scope Resolution

Scope resolution combines semantic interpretation with deterministic repository analysis.

```text
User request
     │
     ▼
LLM Scope Interpreter
     │
     ▼
Candidate seeds/entities
     │
     ▼
Deterministic Scope Resolver
     │
     ▼
Candidate Logical Slice
     │
     ▼
LLM Scope Reviewer
     │
     ▼
Deterministic Validation
     │
     ▼
Human Approval
     │
     ▼
Named Persistent Slice
```

---

## 5.1 LLM Scope Interpreter

The first LLM stage interprets semantic intent.

Input may include:

* user request;
* repository structure;
* symbol index;
* routes/endpoints;
* high-level project metadata;
* relevant documentation.

The model must select from repository-known identifiers rather than inventing symbols or paths.

Output:

```text
candidate seeds
candidate entities
semantic concepts
```

Example:

```json
{
  "intent": "checkout workflow",
  "candidate_seeds": [
    "CheckoutController.checkout",
    "CheckoutService.checkout"
  ],
  "candidate_entities": [
    "CartService.validate",
    "InventoryService.reserve",
    "PaymentService.charge",
    "OrderService.create"
  ]
}
```

---

## 5.2 Deterministic Scope Expansion

The resolver expands from grounded seeds using:

* imports/dependencies;
* call graph;
* references;
* data-flow relationships;
* filesystem proximity;
* symbol relationships;
* route/API mappings;
* configuration;
* inheritance/implementation relationships;
* documentation associations.

The output is a candidate logical slice.

---

## 5.3 Membership Must Be Explainable

Membership should not be represented solely by an opaque score.

Example:

```text
InventoryService.reserve

membership:
    CORE

reasons:
    directly called by OrderService.createOrder
    consumes order state
    documented as a checkout step
```

Potential membership signals:

```text
filesystem proximity
import relationship
call relationship
data-flow relationship
documentation relationship
API/route relationship
semantic relationship
```

Scores may be used, but explanations and underlying relationships are authoritative.

---

## 5.4 LLM Scope Review

The candidate slice is presented to an LLM with:

* user intent;
* actual repository entities;
* graph relationships;
* documentation associations.

The LLM classifies entities:

```text
CORE
RELATED
EXCLUDED
```

and provides reasoning.

The LLM proposes; it does not directly mutate the authoritative scope.

---

## 5.5 Deterministic Scope Validation

All structural claims made by the LLM are checked against the repository representation.

For example, if the LLM claims:

```text
CheckoutService → PaymentService
```

the system verifies whether that relationship actually exists.

LLM-generated fictional dependencies must never enter the authoritative graph.

---

## 5.6 Human Approval

Before expensive analysis, the proposed logical slice should be visible to the user.

Example:

```text
Proposed slice: checkout

CORE
✓ CheckoutController.checkout
✓ CheckoutService.checkout
✓ CartService.validate
✓ InventoryService.reserve
✓ PaymentService.charge
✓ OrderService.create
✓ OrderRepository.save

RELATED
? NotificationService.send

EXCLUDED
✗ LoggingService
```

The user can:

* approve;
* exclude;
* add;
* expand;
* rename;
* modify the scope.

After approval, the slice becomes persistent.

---

# 6. Named Persistent Logical Slices

Logical slices are first-class persistent entities.

Example:

```text
slice:
    checkout

identity:
    slice_0192
```

A slice stores:

* name;
* description;
* scope definition;
* member entities;
* membership class;
* membership score;
* membership reasons;
* inclusion/exclusion rules;
* documentation associations;
* analysis history;
* findings;
* repository snapshot relationships.

The same logical slice can be re-evaluated against future repository snapshots.

Example:

```text
checkout@commit-A
checkout@commit-B
checkout@commit-C
```

Slice evolution can therefore be represented.

Example:

```text
Slice evolution:

+ FraudDetectionService

reason:
    newly introduced call/data-flow relationship
```

---

# 7. Program Representation

The internal analysis substrate consists of:

```text
AST
IR
Symbol Table
Call Graph
Control-Flow Graph
Data-Flow Representation
Dominance/Post-Dominance
```

Language-specific frontends may generate language-specific representations, but the detector/evidence layer should consume normalized semantic abstractions.

---

# 8. External Analyzer Integration

External analyzers are a first-class subsystem.

Examples:

```text
Flutter Analyze
ESLint
PHPStan
TypeScript compiler
language-specific compilers
framework analyzers
project-specific linters
```

The system should orchestrate them against the selected repository snapshot and, where practical, the relevant logical slice.

---

## 8.1 Analyzer Adapter

Each analyzer is integrated through an adapter:

```text
AnalyzerAdapter
├── discover()
├── supports(language/project)
├── capabilities()
├── analyze(snapshot, scope)
└── normalize(output)
```

Example adapters:

```text
FlutterAnalyzeAdapter
ESLintAdapter
PHPStanAdapter
TypeScriptAdapter
```

`capabilities()` describes what the analyzer provides.

Example:

```text
flutter_analyze:
    type diagnostics
    undefined symbols
    analyzer diagnostics
    lint rules
```

```text
eslint:
    JavaScript/TypeScript lint diagnostics
    AST-based rules
    plugin diagnostics
```

---

## 8.2 Canonical External Diagnostic

Raw analyzer output is normalized into a canonical representation.

Example:

```text
ExternalDiagnostic
├── analyzer
├── analyzer_version
├── rule_id
├── severity
├── message
├── location
├── snapshot
├── configuration
└── raw_diagnostic
```

Example:

```text
analyzer:
    flutter_analyze

rule:
    undefined_method

severity:
    error

location:
    checkout.dart:142
```

The original diagnostic and configuration remain available for provenance.

---

## 8.3 External Diagnostics Are Evidence Providers

External analyzers should not be treated as competing with internal detectors.

Conceptually:

```text
                  Evidence Sources
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
External Analyzers  Internal Analysis  Documentation
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Unified Evidence
                        │
                        ▼
                     Detectors
                        │
                        ▼
                      LLM
```

External diagnostics can therefore:

* become findings directly;
* support another finding;
* participate in detector composition;
* be correlated with internal graph facts;
* be supplied as evidence to the LLM.

---

## 8.4 Avoiding Duplicate Analysis

The system should not reimplement mature analyses merely for architectural consistency.

For example, if Flutter Analyze already provides a reliable unused-variable diagnostic, the initial system should consume that diagnostic rather than building its own duplicate unused-variable detector.

This is particularly important for the initial scope of the system.

Level-1 categories such as:

```text
unreachable code
dead branches
unused values
```

should generally be delegated to established analyzers where available rather than becoming primary custom graph analyses.

The custom engine should concentrate on cross-function, cross-file, path-sensitive, data-flow, workflow, and intent-level problems.

---

# 9. Internal Graphs

## 9.1 Call Graph

Represents invocation relationships:

```text
A.foo()
   │
   ├──► B.bar()
   └──► C.baz()
```

Supports:

* caller discovery;
* callee discovery;
* reachability;
* workflow construction;
* missing-call analysis;
* feature expansion;
* call-path extraction.

---

## 9.2 Control-Flow Graph

CFGs represent intra-function control flow.

They support:

* reachability;
* branch analysis;
* path analysis;
* path conditions;
* dominance;
* post-dominance;
* resource lifecycle analysis;
* conditional data-flow reasoning.

Whole CFGs need not be supplied to the LLM.

Only relevant CFG fragments enter evidence slices.

---

## 9.3 Data-Flow Graph

Data flow is a primary correctness substrate.

It represents:

```text
definition → transformation → use
```

and, where supported:

```text
object.field → transformation → object.field
```

Capabilities should include:

* definitions;
* uses;
* reaching definitions;
* use-def chains;
* argument flow;
* return flow;
* field provenance;
* object shape;
* value provenance;
* producer/consumer relationships.

This is particularly important for subtle correctness defects such as:

* dropped fields;
* missing arguments;
* values that fail to reach consumers;
* values reaching the wrong consumer;
* state being lost across function boundaries.

---

# 10. Dominance and Post-Dominance

Dominance and post-dominance are derived CFG analyses.

Example:

```text
authenticate()
      │
      ▼
privilegedOperation()
```

If `authenticate()` dominates the privileged operation, every path to that operation passes through authentication.

Post-dominance can establish lifecycle properties such as:

```text
open()
  ...
close()
```

where `close()` should post-dominate relevant paths following `open()`.

---

# 11. Deterministic Algorithms

Internal algorithms may include:

```text
BFS
DFS
reachability
path search
dominators
post-dominators
reaching definitions
use-def analysis
data-flow propagation
```

These are implementation details.

The higher-level interfaces expose semantic facts:

```text
can_reach(A, B)
```

rather than:

```text
run_bfs(A, B)
```

The LLM must not need to know whether BFS, DFS, or another algorithm generated a fact.

---

# 12. Evidence API

The Evidence API is a central architectural abstraction.

Detectors should consume semantic evidence queries rather than manipulating graph internals directly.

Representative operations:

```text
get_file(file_id)

get_symbol(symbol_id)

get_references(symbol_id)

get_callers(function_id)

get_callees(function_id)

get_call_path(source, target)

get_reachable_nodes(node)

get_entry_points(scope)

get_exit_points(scope)

get_control_flow(function)

get_paths(source, target)

get_dominators(node)

get_post_dominators(node)

get_branch_conditions(node)

get_path_conditions(source, target)

can_reach(source, target)

must_pass_through(source, target, node)

get_definitions(value)

get_uses(value)

get_reaching_definitions(use)

get_data_flow(source, target)

get_value_provenance(value)

get_field_provenance(object, field)

get_argument_flow(call)

get_return_flow(function)

get_object_shape(value)

get_field_consumers(object, field)

get_field_producers(object, field)
```

External analyzer diagnostics must also be accessible through the Evidence API:

```text
get_external_diagnostics(entity)

get_external_diagnostics(scope)

get_diagnostic(rule_id, location)

get_analyzer_capabilities(analyzer)
```

---

# 13. Documentation API

Documentation is queried through a dedicated abstraction.

Representative operations:

```text
get_docs(entity)

get_related_docs(entity)

get_documented_requirements(entity)

get_documented_invariants(entity)

get_documented_workflow(entity)

get_documented_constraints(entity)

find_docs_for_entities(entity_ids)

find_docs_relevant_to_finding(finding)
```

Documentation should be scoped to the logical slice and, more narrowly, to the entities implicated by each finding.

---

# 14. Detector Architecture

Detectors are independent consumers of the Evidence API.

A detector should not:

* construct LLM prompts;
* retrieve arbitrary repository files;
* implement its own graph model;
* know how evidence will be serialized for the LLM.

Instead:

```text
Detector
    │
    ▼
Finding
    │
    ▼
Evidence Requirements
    │
    ▼
Evidence Collector
    │
    ▼
Minimal Evidence Slice
```

---

# 15. Initial Correctness Detector Focus

The first custom detector family should prioritize structural/data-flow/call-flow correctness.

Representative categories:

```text
possible missing call
missing required argument
missing field propagation
value failing to reach expected consumer
unexpected data-flow termination
use-before-definition
possible null/undefined flow
state inconsistency
resource lifecycle violation
suspicious control-flow condition
unexpected workflow deviation
type/shape inconsistency
call/data-flow anomalies
```

These are deliberately different from basic local linting where existing analyzers already provide strong coverage.

---

# 16. Existing Analyzer Findings vs Custom Findings

The system should distinguish source:

```text
source:
    external_analyzer
```

from:

```text
source:
    internal_detector
```

but expose both through a common Finding model.

Example:

```text
Finding
├── id
├── source
├── detector
├── type
├── severity
├── confidence
├── location
├── affected entities
├── evidence requirements
└── status
```

An external analyzer diagnostic can therefore become:

```text
Finding
    source:
        external_analyzer

    analyzer:
        eslint

    rule:
        no-unreachable

    type:
        unreachable_code
```

while a custom detector might produce:

```text
Finding
    source:
        internal_detector

    detector:
        missing_required_field_flow

    type:
        missing_field_propagation
```

Both can participate in later reasoning.

---

# 17. Deferred Analysis Domains

Some detectors require genuinely new analytical domains and should be deferred.

Examples:

```text
taint/security analysis
concurrency/race analysis
specialized numerical analysis
domain-specific semantic analyses
```

These should eventually extend the analysis substrate and expose their facts through the Evidence API.

They should not bypass the architecture.

---

# 18. Detector Composition

Detector composition is a future capability, with higher priority than entirely new analysis domains.

Example:

```text
Detector A
    +
Detector B
    +
Detector C
       │
       ▼
Compound Finding
```

Example:

```text
Finding A:
    field `role` is dropped

Finding B:
    authorization depends on `role`

Finding C:
    authorization occurs after the data loss

Compound finding:
    missing data flow may produce incorrect authorization behavior
```

Individual detector findings remain independently explainable; composition provides higher-order correlation.

External analyzer findings should also eventually participate in this composition model.

---

# 19. Finding Model

A finding is distinct from its evidence.

Conceptual model:

```text
Finding
├── id
├── source
├── detector
├── type
├── classification
├── severity
├── confidence
├── location
├── affected entities
├── evidence requirements
├── snapshot
└── status
```

Possible statuses:

```text
new
confirmed
rejected
false_positive
documentation_outdated
intended_behavior
resolved
```

The detector establishes a candidate finding; the Evidence Engine materializes supporting evidence.

---

# 20. Minimal Evidence Slice

`MinimalEvidenceSlice` is a first-class domain object.

Conceptually:

```text
MinimalEvidenceSlice
├── finding
├── program entities
├── call edges
├── control-flow fragments
├── data-flow fragments
├── external diagnostics
├── relevant conditions
├── documentation
└── provenance
```

The collector should aggressively minimize context.

The optimization target is:

> **Minimum sufficient evidence, not maximum available context.**

---

# 21. Evidence Construction Example

Suppose a detector identifies:

```text
POSSIBLE_MISSING_FIELD

field:
    order.phone
```

The Evidence Engine retrieves:

```text
Producer:
    request.phone

Transformation:
    OrderDTO

Expected consumer:
    OrderRepository.insert

Observed flow:
    request.phone
        ↓
    OrderDTO
        X
        ↓
    Repository.insert
```

Relevant documentation:

```text
docs/orders.md

Invariant:
    phone is required for an order
```

Potential external diagnostic:

```text
PHPStan:
    possible invalid property access
```

The minimal evidence slice contains only the relevant program facts, diagnostic, documentation, and provenance.

---

# 22. Documentation vs Program Evidence

The LLM must explicitly distinguish:

### Program facts

Mechanically observed.

```text
OrderService.createOrder calls OrderRepository.save.
```

### External analyzer facts

Produced by an established analysis tool.

```text
PHPStan reports a possibly undefined property at OrderDTO.php:31.
```

### Derived facts

Mechanically derived by the internal engine.

```text
There exists a path from validation to persistence on which
inventory reservation is absent.
```

### Documentation facts

Statements about intended behavior.

```text
Inventory must be reserved before persistence.
```

### Hypotheses

Semantic interpretations.

```text
The implementation may violate the documented order lifecycle.
```

These epistemic categories must not be collapsed.

---

# 23. LLM Analysis

The LLM receives:

```text
Finding
+
Minimal Program Evidence
+
Relevant External Diagnostics
+
Relevant Documentation
+
Provenance
```

It performs:

1. evidence comparison;
2. implementation-vs-intent analysis;
3. contradiction detection;
4. correlation of independent evidence;
5. defect likelihood assessment;
6. explanation;
7. uncertainty classification;
8. optional remediation proposal.

The LLM must not infer that:

```text
documentation says X
```

automatically means:

```text
code must do X
```

Nor:

```text
documentation does not mention X
```

means:

```text
X is incorrect.
```

Documentation is an intent signal whose reliability must itself be considered.

---

# 24. Example: Missing Workflow Operation

Documentation:

```text
"An order must reserve inventory before persistence."
```

Program call path:

```text
OrderController.create
    ↓
OrderService.createOrder
    ↓
validateOrder
    ↓
OrderRepository.save
```

Expected operation:

```text
InventoryService.reserve
```

is absent from the observed path.

Internal detector:

```text
POSSIBLE_MISSING_CALL
```

Evidence:

```text
call path
+
reachable paths
+
relevant CFG conditions
+
documentation invariant
```

Potential external evidence may also be included.

The LLM receives:

```text
documented intent:
    reserve before persist

observed behavior:
    persist without reserve

supporting graph facts:
    ...

external diagnostics:
    ...

conclusion:
    likely implementation/intent discrepancy
```

The graph engine establishes the structural facts; the LLM performs the semantic judgment.

---

# 25. Storage Architecture

SQLite is the authoritative persistence layer for analysis metadata and relationships.

Recommended project layout:

```text
project/
└── .codeanalyzer/
    ├── analysis.db
    ├── graphs/
    ├── snapshots/
    └── cache/
```

SQLite should store:

* project metadata;
* snapshots;
* entities;
* relationships;
* slices;
* analysis runs;
* findings;
* evidence metadata;
* documentation associations;
* analyzer diagnostics.

Large derived graph artifacts may be materialized separately.

The filesystem is therefore an artifact/cache layer, not the authoritative relational model.

---

# 26. Conceptual Database Model

```text
projects
────────────
id
path
name
created_at


snapshots
────────────
id
project_id
commit_hash
created_at


entities
────────────
id
snapshot_id
type
name
file
start_line
end_line


relationships
────────────
source_id
target_id
type


logical_slices
────────────
id
snapshot_id
name
description
created_at


slice_members
────────────
slice_id
entity_id
membership_type
score
reason


analyses
────────────
id
slice_id
snapshot_id
created_at
status


external_diagnostics
────────────
id
analysis_id
analyzer
analyzer_version
rule_id
severity
message
location
configuration
raw_payload


findings
────────────
id
analysis_id
source
detector
type
severity
confidence
status
location


evidence_slices
────────────
id
finding_id
created_at


evidence_items
────────────
evidence_slice_id
type
entity_id
source
location
payload


documentation
────────────
id
snapshot_id
source
location
content


doc_entities
────────────
doc_id
entity_id
relationship
```

The exact schema is implementation-dependent.

---

# 27. Repository Snapshots

Every analysis must be associated with a repository snapshot.

Preferably:

```text
snapshot
    commit_hash = abc123
```

Then:

```text
slice
    ↓
analysis
    ↓
finding
    ↓
evidence
```

all retain snapshot identity.

This prevents historical findings from becoming ambiguous after source changes.

It also enables:

```text
analysis@commit-A
analysis@commit-B
```

comparison.

Analyzer versions and relevant configurations should also be retained because analyzer output can change independently of source.

---

# 28. Incremental Analysis

Persistent slices enable incremental analysis.

```text
new commit
    │
    ▼
changed entities
    │
    ▼
affected graph regions
    │
    ▼
affected logical slices
    │
    ▼
invalidate/recompute necessary analyses
```

Unchanged representations and analyzer results may be reused when sound.

A named slice survives source changes, but its membership and analyses must be revalidated against the new snapshot.

---

# 29. Scope vs Evidence Optimization

The system must distinguish:

### Scope optimization

> What code is necessary to understand this feature?

from:

### Evidence minimization

> What code/data/documentation is necessary to evaluate this particular finding?

A logical slice may contain hundreds of entities.

One finding may require:

```text
4 functions
7 graph edges
1 data-flow chain
2 path conditions
1 external diagnostic
1 documentation statement
```

Only that subset should normally reach the LLM.

---

# 30. End-to-End Operational Flow

```text
1. User selects/describes a feature
                    │
                    ▼
2. LLM interprets semantic intent
                    │
                    ▼
3. Candidate seeds are grounded to repository entities
                    │
                    ▼
4. Deterministic scope resolver expands candidates
                    │
                    ▼
5. Candidate logical slice is constructed
                    │
                    ▼
6. LLM reviews semantic scope
                    │
                    ▼
7. Deterministic validation checks structural claims
                    │
                    ▼
8. User approves/edits
                    │
                    ▼
9. Named persistent slice is stored
                    │
                    ▼
10. Program representation is generated
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
11a. Existing analyzers    11b. Internal analysis
          │                   │
          │             AST / IR / CFG
          │             Call Graph
          │             Data Flow
          │             Dominance
          │                   │
          └─────────┬─────────┘
                    ▼
12. Unified evidence/diagnostics
                    │
                    ▼
13. Detectors produce findings
                    │
                    ▼
14. Evidence requirements generated
                    │
                    ▼
15. Evidence Collector constructs
    Minimal Evidence Slice
                    │
              ┌─────┴─────┐
              ▼           ▼
        Program Facts   Documentation
              │           │
              └─────┬─────┘
                    ▼
16. LLM evaluates implementation vs intent
                    │
                    ▼
17. Final result stored
                    │
                    ▼
18. Developer confirms/rejects/resolves
```

---

# 31. Stable Architectural Interfaces

The primary stable interfaces are:

```text
Scope API
Analyzer Adapter API
Evidence API
Documentation API
Detector API
Finding Model
MinimalEvidenceSlice
Analysis/Snapshot API
```

## Scope API

Answers:

```text
What belongs to the logical feature?
```

## Analyzer Adapter API

Answers:

```text
What does an existing ecosystem analyzer report?
```

## Evidence API

Answers:

```text
What does the program structurally establish?
```

## Documentation API

Answers:

```text
What is documented/intended?
```

## Detector API

Answers:

```text
What structural anomaly is interesting?
```

## Finding Model

Represents:

```text
What may be wrong?
```

## MinimalEvidenceSlice

Represents:

```text
What evidence is sufficient to investigate it?
```

## LLM

Determines:

```text
What do these facts mean semantically?
```

---

# 32. Initial Non-Goals

The initial system should not attempt to:

* send whole repositories to an LLM;
* have the LLM discover graph structure from raw source;
* make the LLM authoritative over repository structure;
* duplicate mature analyzer functionality unnecessarily;
* implement every possible static-analysis domain;
* maintain independent graph representations for every algorithm;
* expose BFS/DFS implementation details to detectors or the LLM;
* produce maximal context for every finding;
* treat documentation as ground truth;
* treat missing documentation as proof of incorrectness;
* implement detector composition in the first implementation;
* require every detector to operate over every available analysis.

---

# 33. Implementation Roadmap

## Phase A — Repository and program substrate

Implement:

```text
language frontend(s)
AST / IR
symbol resolution
call graph
CFG
data flow
snapshot model
SQLite persistence
```

---

## Phase B — External Analyzer Layer

Implement:

```text
AnalyzerAdapter interface
process execution
tool discovery
configuration capture
diagnostic normalization
version capture
provenance
```

Initial integrations should prioritize the ecosystems the system targets.

For Flutter:

```text
flutter analyze
```

For JavaScript/TypeScript:

```text
ESLint
TypeScript compiler
```

For PHP:

```text
PHPStan
```

Additional analyzers can follow without changing the core architecture.

---

## Phase C — Scope Engine

Implement:

```text
seed resolution
filesystem discovery
symbol discovery
graph expansion
documentation association
LLM semantic seed interpretation
LLM scope review
scope validation
named persistent slices
```

---

## Phase D — Evidence Architecture

Implement:

```text
Evidence API
typed evidence
provenance
External Diagnostic API
Documentation API
Evidence Collector
MinimalEvidenceSlice
```

This is architecturally critical.

---

## Phase E — Initial Correctness Detectors

Prioritize:

```text
missing data/field flow
missing argument
possible missing call
use-before-definition
possible null/undefined flow
state/control-flow inconsistency
resource lifecycle violations
call/data-flow anomalies
workflow deviations
```

Basic local issues already handled well by existing analyzers should generally remain delegated.

---

## Phase F — LLM Reasoning

Implement:

```text
finding → evidence requirements
evidence-slice construction
documentation retrieval
external diagnostic retrieval
implementation/intention comparison
cross-evidence correlation
confidence/uncertainty
finding explanation
optional remediation
```

---

## Phase G — Detector Composition

Higher-priority future capability:

```text
internal finding
+
internal finding
+
external diagnostic
+
data-flow fact
→
compound finding
```

---

## Phase H — New Analysis Domains

Later:

```text
taint/security analysis
concurrency analysis
specialized numerical analysis
domain-specific semantic analyses
```

These extend the existing evidence substrate.

---

# 34. Fundamental Design Invariant

The system should preserve this chain:

```text
User Intent
     ↓
Logical Scope
     ↓
Program Representation
     ↓
External + Internal Analysis
     ↓
Program/Analyzer Facts
     ↓
Deterministic Finding
     ↓
Minimal Evidence
     ↓
Documented Intent
     ↓
LLM Judgment
```

Each transition has an explicit interface and provenance.

The system should never collapse into:

```text
source code → LLM → "probably buggy"
```

The intended architecture is:

```text
                 ┌──────────────────────┐
                 │ Existing Analyzers   │
                 │ Flutter / ESLint /   │
                 │ PHPStan / TS / ...  │
                 └──────────┬───────────┘
                            │
                            ▼
Source → Program Model → Unified Evidence
                            ▲
                            │
                 ┌──────────┴───────────┐
                 │ Internal Analysis    │
                 │ CFG / Call / Data    │
                 │ Flow / Dominance     │
                 └──────────────────────┘
                            │
                            ▼
                       Detectors
                            │
                            ▼
                         Finding
                            │
                            ▼
                  Minimal Evidence Slice
                            │
                   ┌────────┴────────┐
                   ▼                 ▼
              Program Facts     Documentation
                   │                 │
                   └────────┬────────┘
                            ▼
                           LLM
                            │
                            ▼
                     Semantic Judgment
```

---

# 35. Architectural Thesis

The system is fundamentally a **program-evidence integration and reasoning engine**, not an LLM code-reviewer and not a replacement for existing static-analysis tooling.

Its principal abstractions are:

**Existing analyzers**
→ established language/framework knowledge that should be reused rather than unnecessarily reimplemented.

**Program graph**
→ deterministic representation of structural behavior.

**Evidence API**
→ semantic interface over internal graphs and external diagnostics.

**Named Persistent Logical Slice**
→ durable representation of the feature/module/workflow being analyzed.

**Finding**
→ a concrete suspected correctness problem produced from deterministic or external evidence.

**MinimalEvidenceSlice**
→ the smallest defensible evidence set needed to investigate that finding.

**Documentation**
→ explicit representation of intended behavior and contracts.

**LLM**
→ semantic reasoning layer that compares implementation evidence with intended behavior and correlates heterogeneous evidence.

The central correctness distinction is:

```text
Observed behavior
        vs
Documented intent
```

The central scalability mechanism is:

```text
Repository
    ↓
Logical Slice
    ↓
Finding
    ↓
Minimal Evidence Slice
    ↓
LLM
```

And the central integration principle is:

```text
Do not rebuild mature analysis.
Do not blindly trust it either.
Normalize it into evidence.
Correlate it with broader program facts.
Then reason over the combined evidence.
```

The resulting system can therefore operate at increasing levels of semantic sophistication:

```text
Local analyzer diagnostic
        ↓
Cross-file graph fact
        ↓
Cross-function data-flow finding
        ↓
Workflow-level structural discrepancy
        ↓
Implementation-vs-documentation contradiction
        ↓
Compound, semantically reasoned correctness finding
```

without requiring the LLM to ingest the entire repository or requiring the custom engine to duplicate the entire static-analysis ecosystem.
