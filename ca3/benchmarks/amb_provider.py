from __future__ import annotations

from pathlib import Path
from typing import Any

from ca3.memory_backend import InMemoryMemoryBackend, tokenize


class Ca3OpenMemoryBenchmarkProvider:
    """Open Memory Benchmark provider adapter for ca3.

    This class intentionally uses the same method/attribute shape as
    ``memory_bench.memory.base.MemoryProvider`` without importing OMB at ca3 test
    time. The install script creates a tiny OMB-side subclass wrapper so the
    public harness can instantiate it from its registry.
    """

    name = "ca3"
    description = "CA3 deterministic local MemoryBackend provider for Open Memory Benchmark integration."
    kind = "local"
    provider = "ca3"
    variant = "local"
    concurrency = 1

    def __init__(self, backend: InMemoryMemoryBackend | None = None) -> None:
        self.backend = backend or InMemoryMemoryBackend()
        self.store_dir: Path | None = None
        self.unit_ids: set[str] | None = None

    def prepare(self, store_dir: str | Path, unit_ids: set[str] | None = None, reset: bool = True) -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.unit_ids = set(unit_ids) if unit_ids is not None else None
        if reset:
            self.backend = InMemoryMemoryBackend()

    def ingest(self, documents: list[Any]) -> None:
        for document in documents:
            self.backend.write(
                session_id=getattr(document, "user_id", None) or "__default__",
                text=getattr(document, "content"),
                metadata={
                    "omb_document_id": getattr(document, "id", None),
                    "user_id": getattr(document, "user_id", None),
                    "timestamp": getattr(document, "timestamp", None),
                    "context": getattr(document, "context", None),
                    "messages": getattr(document, "messages", None),
                },
            )

    def retrieve(
        self,
        query: str,
        k: int = 10,
        user_id: str | None = None,
        query_timestamp: str | None = None,
    ) -> tuple[list[Any], dict[str, Any]]:
        query_tokens = tokenize(query)
        scored = []
        for record in self.backend._records:
            record_user_id = record.metadata.get("user_id")
            if user_id is not None and record_user_id != user_id:
                continue
            overlap = len(query_tokens & tokenize(record.text))
            if overlap > 0:
                scored.append((-overlap, record.id, record))
        scored.sort(key=lambda item: (item[0], item[1]))
        records = [record for _, _, record in scored[:k]]
        raw_response = {
            "memory_provider": self.name,
            "query": query,
            "k": k,
            "user_id": user_id,
            "query_timestamp": query_timestamp,
            "returned": len(records),
            "retrieved_ids": [str(record.metadata.get("omb_document_id", record.id)) for record in records],
            "scoring_note": "public score must come from Open Memory Benchmark harness, not ca3 local fixtures",
        }
        return records, raw_response


def records_to_omb_documents(records: list[Any], document_cls: type[Any]) -> list[Any]:
    """Convert ca3 MemoryRecord objects into OMB Document objects."""

    return [
        document_cls(
            id=str(record.metadata.get("omb_document_id", record.id)),
            content=record.text,
            user_id=record.metadata.get("user_id"),
            messages=record.metadata.get("messages"),
            timestamp=record.metadata.get("timestamp"),
            context=record.metadata.get("context"),
        )
        for record in records
    ]
