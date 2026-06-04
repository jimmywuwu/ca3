# ca3

MemoryBackend implementation workspace for the `peer` tick-based Agent Loop experiment.

## Execution model

- Jayda remains the MemoryBackend architecture and discussion profile.
- `peerworker` is Jayda's isolated implementation worker, not a separate strategy collaborator.
- `peer` owns the tick protocol, request/contract state, reusable workflow definitions, and worker dispatch traces.
- Jayda reviews worker traces/artifacts before they become durable architecture decisions or memory.
- Future specialized agents may reuse the workflows proven here, but this phase only needs one executor path.

This repository is intentionally separate from `peer`:

- `peer`: Agent Loop runtime and collaboration protocol.
- `ca3`: MemoryBackend product / implementation code.

## Success target

The MemoryBackend goal is benchmark leadership on memory-agent evaluations such as MemoryAgentBench / Agent Memory Benchmark, MemoryArena, and STATE-Bench. See [`docs/success-metrics.md`](docs/success-metrics.md) and [`docs/benchmark-regression-gate.md`](docs/benchmark-regression-gate.md).

## Current status

Initial workspace marker plus a local no-model benchmark smoke harness. Concrete implementation should be created through bounded `peerworker` execution ticks, not by mixing implementation context directly into Jayda's long-running architecture conversation.

## Local benchmark smoke

Run the first simple no-model scoring-flow smoke harness:

```bash
python3 -m ca3.benchmarks.smoke --output benchmark-results/smoke/latest.json
```

The command writes a JSON score report with per-benchmark scores and an aggregate summary, for example:

```text
Score: ca3=1.000, baseline=0.000, delta=1.000
```

The harness uses only stdlib code: an in-memory deterministic lexical MemoryBackend, local fixtures, and exact/gold-containment scoring. It exercises three benchmark-shaped flows without external LLM, model, embedding, or network calls:

- MemoryArena-like cross-session state recall.
- STATE-Bench-like procedural learning retrieval for a held-out task.
- AMB-like document ingest, retrieval, deterministic answer, and gold containment judging.

Run tests with:

```bash
python3 -m pytest tests -q
```
