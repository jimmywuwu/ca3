# MemoryBackend Success Metrics

This document is Jayda's success rubric for `peerworker` while building the MemoryBackend implementation in `ca3`.

## Corrected project framing

`peerworker` is not a peer collaborator and this phase does not require a collaboration structure.

Current structure:

```text
Jimmy ↔ Jayda: MemoryBackend architecture, product judgment, benchmark strategy
Jayda → peer: reusable workflow / bounded commitment definition
peer → peerworker: implementation execution in ca3
peerworker → peer/Jayda: artifacts, tests, traces, blockers
```

The success metric is Jayda's ability to define reusable work protocols that future agents can follow. Different agents may later have finer role-specific workflows, but the first objective is to prove one clean executor path with `peerworker`.

## North-star objective

MemoryBackend should become a benchmark-leading memory substrate for bounded agents.

Target:

```text
Achieve #1 performance on memory-agent benchmarks such as MemoryAgentBench and MemoryArena.
```

The product should not be optimized merely for storing more text. It should optimize for agent task success under realistic memory pressure:

- remembering the right facts;
- excluding stale or misleading facts;
- maintaining temporal validity;
- preserving provenance;
- supporting cross-session task continuity;
- avoiding unreviewed worker-output contamination;
- assembling compact context packets that improve downstream agent decisions.

## Benchmark-first operating principle

Every MemoryBackend feature should answer at least one of these questions:

1. Does this improve benchmark score?
2. Does this reduce a known memory failure mode in benchmark-like scenarios?
3. Does this make benchmark failures easier to diagnose and repair?
4. Does this generalize into a reusable workflow for future agents?

If the answer is no, the feature is secondary.

## Top-level success metrics

### 1. Benchmark rank

Primary external target:

```text
MemoryAgentBench rank: #1
MemoryArena rank: #1
```

Until full benchmark integration exists, use local benchmark-shaped scenarios as proxies.

### 2. Reusable workflow quality

`peerworker` should help Jayda produce workflows that future agents can reuse.

Success indicators:

- tasks have explicit request IDs, scope, non-goals, and success criteria;
- worker reports are structured and reviewable;
- implementation steps can be replayed or adapted by another specialized worker;
- workflow templates are not tied to `peerworker` personality/context;
- context needed for execution is supplied by the workflow, not assumed from chat history.

### 3. Memory decision quality

MemoryBackend should classify and govern memory records correctly.

Core classes:

- durable fact;
- user/project preference;
- architectural decision;
- hypothesis;
- task state;
- worker trace;
- temporary note;
- archived context.

Success indicators:

- stale task state is not retrieved as active truth;
- hypotheses are not treated as decisions;
- worker traces do not become durable memory before review;
- provenance is available for every retrieved item;
- temporal validity is explicit.

### 4. Context packet precision

MemoryBackend should build context packets that are small, relevant, and explainable.

A context packet should include:

- memories included;
- memories excluded;
- rationale for inclusion/exclusion;
- token/size budget;
- provenance references;
- temporal validity notes.

Primary metric:

```text
High precision under a fixed context budget.
```

### 5. Trace reconstruction

Given a multi-tick run, MemoryBackend should reconstruct what happened.

Minimum reconstruction questions:

- what did the agent know at each tick?
- what request or task was active?
- what memories were retrieved?
- what memories were written or rejected?
- what worker artifact was produced?
- what review decision happened afterward?

## Phase 1 success criteria for peerworker

By the end of Phase 1, `ca3` should contain a minimal benchmark-oriented MemoryBackend core that can:

1. define memory records with kind, provenance, confidence, temporal validity, and review status;
2. persist tick traces and worker traces;
3. build a context packet for a benchmark-like memory task;
4. exclude stale, rejected, or unreviewed records from durable context;
5. run local benchmark-shaped tests;
6. expose a workflow/report format that future specialized agents can reuse.

## Phase 1 measurable checklist

- [ ] Python package scaffold exists.
- [ ] Test command is documented.
- [ ] `MemoryRecord` model exists.
- [ ] `MemoryKind` enum exists.
- [ ] `ReviewStatus` enum exists.
- [ ] `TemporalValidity` or equivalent exists.
- [ ] `TraceRecord` / `TickTrace` model exists.
- [ ] `WorkerTrace` model exists.
- [ ] Context packet builder exists.
- [ ] Tests cover stale-memory exclusion.
- [ ] Tests cover unreviewed-worker-trace exclusion.
- [ ] Tests cover hypothesis vs durable-fact distinction.
- [ ] Tests cover provenance on retrieved memory.
- [ ] Tests cover benchmark-shaped multi-session recall.

## Benchmark-shaped local evals before official integration

Before direct MemoryAgentBench / MemoryArena adapters exist, `peerworker` should implement local scenarios that approximate likely benchmark pressures:

### Scenario A: Long-horizon preference recall

The agent receives facts across multiple sessions and must later use only the currently valid preference.

Pass condition:

- retrieves current preference;
- excludes superseded preference;
- explains temporal reasoning.

### Scenario B: Task continuity under noise

The agent must continue a task after irrelevant events and worker traces were logged.

Pass condition:

- retrieves active task state;
- excludes unrelated worker noise;
- preserves request ID and success criteria.

### Scenario C: Contradictory memory resolution

Two memories conflict.

Pass condition:

- uses provenance, timestamp, confidence, and review status to select or flag uncertainty;
- does not silently merge contradiction into a false summary.

### Scenario D: Review-gated worker artifact

A worker produces an implementation note.

Pass condition:

- note is searchable as trace;
- note is not eligible as durable architecture memory until reviewed.

### Scenario E: Benchmark replay trace

A benchmark task fails.

Pass condition:

- system can show retrieved memories, excluded memories, and scoring-relevant decisions for debugging.

## Anti-goals

`peerworker` should avoid:

- building a generic vector DB wrapper as the whole product;
- optimizing for memory volume instead of task success;
- creating multi-agent collaboration machinery before reusable single-worker workflows are proven;
- letting implementation notes become product direction;
- adding cloud dependencies before local benchmark loops work.

## One-sentence worker objective

Build `ca3` into a benchmark-leading governed memory layer for bounded agents, starting with reusable single-worker workflows and local evals that can later target MemoryAgentBench and MemoryArena directly.
