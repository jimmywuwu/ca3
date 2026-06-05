# Benchmark Regression Gate

Every meaningful MemoryBackend design iteration should produce benchmark evidence, not just architectural notes.

This document tracks the benchmark suite that `ca3` should integrate as the MemoryBackend matures.

## Goal

Use external benchmark runs as release evidence:

- prove each MemoryBackend design revision improves or preserves measured behavior;
- catch regressions in retrieval quality, state handling, latency, and cost;
- make benchmark results comparable across versions;
- prioritize improvements that move public leaderboards, not just local abstractions.

## Benchmark families

### 1. MemoryArena

Source:

- Paper: https://arxiv.org/pdf/2602.16313
- Site: https://memoryarena.github.io/
- Repo: https://github.com/ZexueHe/MemoryArena
- Dataset: `ZexueHe/memoryarena`

What it measures:

- multi-session agentic tasks;
- memory updates between subtasks/sessions;
- later action success depending on earlier session traces;
- domains: bundled shopping, group travel planning, progressive search, formal reasoning math, formal reasoning physics.

Primary metrics:

- SR: task success rate;
- PS: progress score;
- sPS: soft progress score for group travel.

`ca3` integration shape:

- implement dataset adapters for `ZexueHe/memoryarena`;
- implement MemoryArena-compatible memory server endpoints:
  - `POST /memory/initialize`
  - `POST /memory/add`
  - `POST /memory/wrap_user_prompt`
- treat `add` as session-boundary trace ingestion, not merely arbitrary text append;
- begin with progressive search and formal reasoning before full shopping/travel integration.

### 2. STATE-Bench

Source:

- Blog: https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/
- Repo: https://github.com/microsoft/STATE-Bench

What it measures:

- realistic enterprise workflows where agents mutate stateful environments;
- domains: travel, customer support, shopping assistant;
- memory/learning improves production-like task execution, not just recall.

Tracks:

- Main Track: direct agent/model evaluation;
- Agent Learning Track: memory, skills, or prompt optimization from train trajectories.

Most relevant for `ca3`:

- Agent Learning Track.

Official Agent Learning shape:

- use `datasets/train_task_trajectories/<domain>/` to build reusable learnings;
- expose retrieval via `retrieve_learnings(query, top_k=3) -> list[str]`;
- run held-out test tasks with `--num-runs 5`;
- do not use held-out test definitions/environments as oracle inputs;
- retrieval is read-only during evaluation.

Primary metrics:

- Task Completion pass@1: average completion rate across five runs per task;
- Task Completion pass^5: percentage of tasks succeeding in all five runs;
- UX Score: LLM-judged conversation quality on a 1-5 rubric;
- Cost Per Task: reported agent cost from token usage/pricing.

`ca3` integration shape:

- build a STATE-Bench learning artifact from train trajectories;
- implement a thin `StateBenchAgent` subclass whose `retrieve_learnings` calls `ca3`;
- benchmark each design revision against no-memory and previous `ca3` versions;
- preserve protocol compliance: locked simulator/judge, unchanged tasks/tools/prompts, official `top_k=3`, official five-run setting for publishable numbers.

### 3. AMB / Open Memory Benchmark

Sources:

- Leaderboard/site: https://agentmemorybenchmark.ai/
- Main site repo: https://github.com/vectorize-io/agent-memory-benchmark
- Harness repo: https://github.com/vectorize-io/open-memory-benchmark

What it measures:

- memory and retrieval systems over long-context personal conversations, agent trajectories, and time-sensitive knowledge;
- currently includes datasets such as BEAM, LifeBench, LoCoMo, LongMemEval, PersonaMem, AMA-Bench, MemSim, MemBench.

Modes:

- `rag`: provider retrieves top-k documents, then an LLM answers from injected context;
- `agentic-rag`: LLM can use a recall tool multiple times;
- `agent`: provider implements native `direct_answer`.

Primary metrics/artifacts:

- accuracy;
- ingestion time;
- retrieval time;
- context tokens;
- per-query result records with judge reasons.

Provider interface shape:

- implement `MemoryProvider` with:
  - `prepare(store_dir, unit_ids=None, reset=True)` optional;
  - `ingest(documents: list[Document])`;
  - `retrieve(query, k=10, user_id=None, query_timestamp=None) -> (list[Document], raw_response)`;
  - optional `direct_answer(query, user_id=None, query_timestamp=None)` for agent mode.

`ca3` integration shape:

- implement an Open Memory Benchmark provider wrapper for `ca3`;
- start in `rag` mode, then evaluate `agentic-rag` and native `agent` mode if `ca3` develops its own answer/context synthesis;
- always record speed/cost alongside accuracy.

## Release evidence policy

For every meaningful MemoryBackend design revision:

1. Record a version label, commit SHA, config, model, and benchmark harness commit.
2. Run a smoke subset before full benchmark runs.
3. Compare against:
   - no-memory baseline where available;
   - simple BM25/hybrid retrieval baseline;
   - previous `ca3` release candidate.
4. Store results under a versioned benchmark-results directory.
5. Report both score improvements and cost/latency regressions.
6. Do not claim improvement from a single noisy run if the benchmark protocol requires repeated runs.

## Suggested maturity ladder

### Phase A: Interface smoke gates, not benchmark evidence

- MemoryArena dataset adapter tests;
- AMB provider interface tests with inline fixtures;
- STATE-Bench learning retrieval hook tests without full expensive runs.

These gates may emit local fixture scores, but those scores are only `interface_smoke`. They must not be reported as benchmark progress or compared to benchmark baselines.

### Phase B: Cheap public-harness subsets

- AMB `personamem` or another small split with `--query-limit`;
- MemoryArena selected progressive search / formal reasoning subset;
- STATE-Bench single-domain small internal run if supported by local config.

### Phase C: Full benchmark runs

- MemoryArena full target domains;
- AMB selected leaderboard splits;
- STATE-Bench Agent Learning Track with official `--num-runs 5`.

### Phase D: Release gate

A `ca3` design revision is release-worthy only if it has one of:

- a clear benchmark improvement under fixed cost/latency budget;
- equal score with materially lower cost/latency/complexity;
- a targeted regression fix proven on the relevant benchmark slice.

## Design implications

These benchmarks collectively push `ca3` toward three capabilities:

1. **Session/action memory** — MemoryArena requires cross-session task continuity.
2. **Reusable learnings** — STATE-Bench requires extracting procedural learnings from prior trajectories and retrieving them at inference time.
3. **Retrieval precision under budget** — AMB requires accurate, fast, cheap retrieval over long-context memory corpora.

Therefore `ca3` should expose a common internal lifecycle:

```text
observe trace/documents
→ classify/distill memories or learnings
→ index with provenance, scope, timestamp, and validity
→ retrieve/contextualize under budget
→ emit traceable context packet
→ evaluate score, latency, cost, and failure reasons
```

The product should not optimize for one benchmark in isolation. The target is a memory layer whose behavior improves across all three families.