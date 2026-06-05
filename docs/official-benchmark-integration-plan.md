# Official Benchmark Integration Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Replace misleading local fixture scores with protocol-compliant benchmark integration paths for MemoryArena, STATE-Bench Agent Learning, and AMB/Open Memory Benchmark.

**Architecture:** Local tests remain useful only as interface and regression guards. Real benchmark evidence must come from the public harnesses/datasets, with recorded harness commit, ca3 commit, model/config, baseline, score, latency/cost, and saved result artifacts.

**Tech Stack:** Python, pytest, HuggingFace datasets for MemoryArena, MemoryArena memory HTTP API, Microsoft STATE-Bench `uv` harness, Vectorize Open Memory Benchmark `uv` harness.

---

## Correction: benchmark score vs test/smoke score

The existing `ca3.benchmarks.amb_local` runner is an **interface smoke gate**, not a benchmark score. It is valuable because it proves `prepare → ingest → retrieve/direct_answer → score report` can execute, but it must not be used as evidence that MemoryBackend quality improved.

A score becomes benchmark evidence only when it is produced by one of these external protocols:

- MemoryArena runner/dataset with SR / PS / sPS.
- STATE-Bench Agent Learning Track with locked simulator/judge and `--num-runs 5`.
- AMB/Open Memory Benchmark harness with public dataset/domain, answer generation, judge, and output JSON.

Every report must include:

- `ca3_commit`
- `benchmark_name`
- `benchmark_repo` and `benchmark_commit`
- `dataset`, `domain`, `split` or equivalent
- `model` and config
- baseline(s): no-memory, BM25/hybrid, previous ca3 where available
- official metrics
- latency/cost/context-token fields where available
- result artifact path
- protocol compliance notes

---

## Track 1: AMB / Open Memory Benchmark

### What the docs say

Sources checked:

- `https://agentmemorybenchmark.ai/`
- `https://github.com/vectorize-io/open-memory-benchmark`

Official flow:

1. **Ingest** dataset documents into a memory provider.
2. **Retrieve** context for each query.
3. **Generate** an answer with Gemini from retrieved context.
4. **Judge** answer with a second Gemini call against gold answers.

Official quick command shape:

```bash
uv run amb providers
uv run amb domains --dataset personamem
uv run amb run --dataset personamem --domain 32k --memory bm25 --query-limit 20
```

Results are saved to:

```text
outputs/{dataset}/{memory}/{mode}/{domain}.json
```

Requirements:

```text
GEMINI_API_KEY
Python >= 3.11
```

### What ca3 must implement

Create a real provider inside an Open Memory Benchmark checkout, not just a local lookalike fixture.

Provider shape:

```python
class Ca3MemoryProvider(MemoryProvider):
    name = "ca3"
    kind = "local"

    def prepare(self, store_dir, unit_ids=None, reset=True): ...
    def ingest(self, documents: list[Document]) -> None: ...
    def retrieve(self, query: str, k: int = 10, user_id=None, query_timestamp=None) -> tuple[list[Document], dict]: ...
    def direct_answer(self, query: str, user_id=None, query_timestamp=None) -> tuple[str, str, dict]: ...  # later/agent mode only
```

### First real AMB milestone

**Goal:** Run a small public-harness subset, not a self-authored fixture.

Steps:

1. Clone/pin `vectorize-io/open-memory-benchmark` under an external benchmarks directory.
2. Add a `ca3` provider module that imports the local `ca3` package or installs it editable.
3. Register provider in OMB registry.
4. Run:

```bash
uv run amb run --dataset personamem --domain 32k --memory ca3 --query-limit 20
```

5. Save raw output JSON under:

```text
benchmark-results/amb/{YYYYMMDD}-{ca3_commit}-{omb_commit}/personamem-32k-query20.json
```

6. Also run at least one baseline:

```bash
uv run amb run --dataset personamem --domain 32k --memory bm25 --query-limit 20
```

7. Compare accuracy, ingest time, retrieval time, context tokens, and judge reasons.

### Publishable AMB score criteria

Do not call it a real AMB score unless:

- it uses the OMB harness;
- it uses a public AMB dataset/domain;
- it uses configured Gemini generation/judging;
- it stores OMB output artifacts;
- it records `GEMINI_API_KEY` presence only as a yes/no, never the secret;
- it compares with baseline and previous ca3.

---

## Track 2: STATE-Bench Agent Learning

### What the docs say

Sources checked:

- `https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/`
- `https://github.com/microsoft/STATE-Bench`
- `docs/AGENT_LEARNING_TRACK.md`
- `docs/RUN_BENCHMARK.md`

Official Agent Learning Track measures whether reusable learnings from prior trajectories improve held-out enterprise task performance.

Data:

```text
Travel: 100 train trajectories, 50 test tasks
Customer Support: 100 train trajectories, 50 test tasks
Shopping Assistant: 100 train trajectories, 50 test tasks
```

Learning extraction input:

```text
datasets/train_task_trajectories/<domain>/<task_id>.json
```

Retrieval hook:

```python
def retrieve_learnings(query: str, top_k: int = 3) -> list[str]: ...
```

Official run shape:

```bash
uv run python -m state_bench.scripts.run_batch \
  --domain <travel|customer_support|shopping_assistant> \
  --agent-class <YourMemoryAgent> \
  --agent-model-name <model-name> \
  --num-runs 5 \
  --retrieve-learnings-top-k 3 \
  --num-workers <parallel-workers> \
  --output-dir outputs/<domain>/

uv run python -m state_bench.scripts.compute_metrics \
  --domain <domain> \
  --results-dir outputs/<domain>/ \
  --num-runs 5 \
  --output-dir outputs/<domain>/
```

Official metrics:

- Task Completion `pass@1`
- Task Completion `pass^5`
- UX Score
- Cost Per Task

Official compliance:

- only train trajectories can be used for offline learning extraction;
- no held-out test task definitions/environments as oracle inputs;
- locked GPT-5.4 simulator and judge;
- do not edit simulator prompts, judge prompts, domain tools, task files, environment files, or protocol files;
- `--num-runs 5`;
- `--retrieve-learnings-top-k 3`;
- `retrieve_learnings` returns `list[str]`;
- retrieval is read-only during evaluation.

### What ca3 must implement

1. A trajectory reader for STATE-Bench train trajectories.
2. A procedural learning extractor that writes durable `LearningRecord`s with provenance.
3. A `retrieve_learnings(query, top_k=3) -> list[str]` adapter.
4. A repo-local `agents/ca3_learning_agent.py` subclass in the STATE-Bench checkout.
5. A result collector for `metrics.json` and scored trajectories.

### First real STATE-Bench milestone

Because official runs require locked simulator/judge and model configuration, the first milestone is a dry integration plus one small live domain run only after credentials are configured.

Steps:

1. Clone/pin `microsoft/STATE-Bench`.
2. Build ca3 learning artifact from `datasets/train_task_trajectories/travel/`.
3. Add `Ca3LearningAgent(StateBenchAgent)` with `retrieve_learnings`.
4. Run a local import/shape check that validates `retrieve_learnings` returns exactly `list[str]` and respects top_k.
5. Once locked eval/model credentials are configured, run:

```bash
uv run python -m state_bench.scripts.run_batch \
  --domain travel \
  --agent-class Ca3LearningAgent \
  --agent-model-name <model-name> \
  --num-runs 5 \
  --retrieve-learnings-top-k 3 \
  --num-workers 1 \
  --output-dir outputs/travel-ca3/
```

6. Compute metrics and archive:

```text
benchmark-results/state-bench/{YYYYMMDD}-{ca3_commit}-{statebench_commit}/travel/metrics.json
```

### Publishable STATE-Bench score criteria

Do not call it STATE-Bench evidence unless `compute_metrics` succeeds on official outputs with `--num-runs 5` and locked simulator/judge.

---

## Track 3: MemoryArena

### What the docs say

Sources checked:

- arXiv `2602.16313`
- `https://github.com/ZexueHe/MemoryArena`
- HuggingFace dataset `ZexueHe/memoryarena`

MemoryArena is a multi-session agentic benchmark. Each dataset row is a task; each `questions[i]` is a separate session/subtask. Memory starts empty for the episode and is updated between sessions.

Dataset configs observed:

- `bundled_shopping`
- `progressive_search`
- `group_travel_planner`
- `formal_reasoning_math`
- `formal_reasoning_phys`

Official memory API shape:

```text
POST /memory/initialize
POST /memory/add
POST /memory/wrap_user_prompt
```

Metrics:

- SR: Success Rate
- PS: Progress Score
- sPS: soft Progress Score, especially for group travel

### What ca3 must implement

1. Dataset adapter that normalizes HF rows into `MemoryArenaTask -> sessions`.
2. Memory server implementing:
   - `initialize(user_id, memory_system_name)`
   - `add(user_id, memory_system_name, chunk)`
   - `wrap_user_prompt(user_id, memory_system_name, question) -> prompt`
3. Session-boundary memory update semantics.
4. Context packets with included/excluded memories, provenance, validity, and budget.
5. Runner configuration pointing MemoryArena to ca3 memory server.

### First real MemoryArena milestone

Start with adapter + server shape, then run a selected small subset.

Implementation order:

1. Add `ca3.benchmarks.memoryarena.dataset_adapter`.
2. Add `ca3.benchmarks.memoryarena.server` implementing the three official endpoints.
3. Build fixture tests proving each row maps to ordered sessions and memory starts empty per task.
4. Use MemoryArena runner against `progressive_search` or `formal_reasoning_math` small subset.
5. Archive SR/PS outputs under:

```text
benchmark-results/memoryarena/{YYYYMMDD}-{ca3_commit}-{memoryarena_commit}/<domain>/
```

### Publishable MemoryArena score criteria

Do not call it MemoryArena benchmark evidence unless:

- it uses MemoryArena tasks/datasets, not handcrafted fixtures;
- the official runner/environment path is used or clearly documented as a faithful public-harness subset;
- memory is reset per episode;
- each subtask/session only accesses prior information through memory;
- SR/PS/sPS are computed and archived.

---

## Immediate next implementation tasks

### Task 1: Demote local fixture language

**Objective:** Ensure repo docs cannot accidentally present local fixture scores as benchmark results.

**Files:**

- Modify: `README.md`
- Modify: `docs/benchmark-regression-gate.md`

**Acceptance:** Search for `Score: ca3=1.000` and surrounding text must explicitly say `interface smoke`, `local fixture`, and `not benchmark evidence`.

### Task 2: Add benchmark result manifest schema

**Objective:** Make every real run produce comparable metadata.

**Files:**

- Create: `ca3/benchmarks/result_manifest.py`
- Test: `tests/test_benchmark_result_manifest.py`

**Fields:**

```python
benchmark_name: str
dataset: str
domain: str | None
split: str | None
ca3_commit: str
benchmark_repo: str
benchmark_commit: str
model: str | None
config: dict
metrics: dict
baselines: list[dict]
artifact_paths: list[str]
protocol_compliance: dict
notes: str
```

### Task 3: Replace AMB local fixture with real OMB provider integration

**Objective:** Make `ca3` runnable inside `vectorize-io/open-memory-benchmark`.

**Files:**

- Create: `ca3/benchmarks/amb/provider.py` or an integration script that copies/registers provider into an OMB checkout.
- Test: provider shape tests can stay local; score must come from OMB.

**Verification:**

```bash
uv run amb providers
uv run amb run --dataset personamem --domain 32k --memory ca3 --query-limit 20
```

### Task 4: Add STATE-Bench learning adapter

**Objective:** Build and retrieve procedural learnings from train trajectories.

**Files:**

- Create: `ca3/benchmarks/state_bench/learnings.py`
- Create: `ca3/benchmarks/state_bench/agent_adapter.py`
- Test: `tests/test_state_bench_learnings.py`

**Verification:** local tests plus official run only after locked eval/model credentials exist.

### Task 5: Add MemoryArena adapter/server

**Objective:** Implement official MemoryArena memory API surface.

**Files:**

- Create: `ca3/benchmarks/memoryarena/adapter.py`
- Create: `ca3/benchmarks/memoryarena/server.py`
- Test: `tests/test_memoryarena_adapter.py`

**Verification:** local endpoint tests first; official runner subset next.

---

## Working rule going forward

A local test can say:

```text
interface works
```

Only an external benchmark harness can say:

```text
MemoryBackend improved
```

Any future report must use these labels exactly:

- `unit_test`
- `interface_smoke`
- `local_fixture_score`
- `public_harness_subset`
- `official_protocol_run`

Only the last two should be discussed as benchmark evidence, and only `official_protocol_run` should be compared to public leaderboard claims.
