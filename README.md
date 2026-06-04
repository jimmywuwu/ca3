# ca3

MemoryBackend implementation workspace for the `peer` tick-based Agent Loop experiment.

## Collaboration model

- Jayda remains the MemoryBackend architecture and discussion profile.
- `peer` owns the tick protocol, request/contract state, and worker dispatch traces.
- `peerworker` is the isolated Hermes implementation profile that performs concrete repo work here.
- Jayda reviews worker traces/artifacts before they become durable architecture decisions or memory.

This repository is intentionally separate from `peer`:

- `peer`: Agent Loop runtime and collaboration protocol.
- `ca3`: MemoryBackend product / implementation code.

## Current status

Initial workspace marker only. Concrete implementation should be created through bounded `peerworker` execution ticks, not by mixing implementation context directly into Jayda's long-running architecture conversation.
