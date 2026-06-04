from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ca3.memory_backend import InMemoryMemoryBackend, tokenize


@dataclass(frozen=True)
class Document:
    """Lightweight Open Memory Benchmark-shaped document."""

    id: str
    content: str
    user_id: str | None = None
    messages: list[dict[str, Any]] | None = None
    timestamp: str | None = None
    context: str | None = None


@dataclass(frozen=True)
class Query:
    """Local AMB fixture query."""

    id: str
    query: str
    gold: str
    user_id: str | None = None
    query_timestamp: str | None = None
    k: int = 10
    judge: str = "gold_containment"


@dataclass(frozen=True)
class QueryResult:
    """Serializable local result for one AMB-shaped query."""

    query_id: str
    query: str
    user_id: str | None
    gold: str
    answer: str
    context_text: str
    retrieved_ids: list[str]
    passed: bool
    judge: str
    retrieve_time_ms: float
    context_tokens: int
    baseline_answer: str = ""
    baseline_passed: bool = False


@dataclass(frozen=True)
class EvalSummary:
    """Small EvalSummary-like report for local/no-model fixture scoring."""

    total_queries: int
    correct: int
    accuracy: float
    avg_retrieve_time_ms: float
    avg_context_tokens: float
    per_query: list[QueryResult]
    memory_provider: str = "ca3-local"
    mode: str = "agent"
    dataset: str = "amb_local_fixture"
    scoring_mode: str = "local/no-model"
    benchmark_family: str = "agent-memory-benchmark"
    official_leaderboard: bool = False
    no_memory_baseline: dict[str, Any] = field(default_factory=dict)
    delta_vs_baseline: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data["no_memory_baseline"]:
            data["no_memory_baseline"] = {
                "total_queries": self.total_queries,
                "correct": 0,
                "accuracy": 0.0,
            }
        data["delta_vs_baseline"] = data["accuracy"] - data["no_memory_baseline"]["accuracy"]
        return data


class Ca3AMBMemoryProvider:
    """OMB-compatible no-model adapter around ``InMemoryMemoryBackend``.

    This implements the method names used by open-memory-benchmark's provider
    interface while staying purely local and deterministic. It is suitable for
    fixture scoring, not official leaderboard evaluation.
    """

    name = "ca3-local"
    description = "CA3 local deterministic no-model AMB-compatible provider."
    kind = "local"
    provider = "ca3"
    variant = "local-no-model"
    memory_provider = "ca3-local"
    mode = "local/no-model"

    def __init__(self, backend: InMemoryMemoryBackend | None = None) -> None:
        self.backend = backend or InMemoryMemoryBackend()
        self.store_dir: Path | None = None
        self.unit_ids: list[str] | None = None

    def prepare(
        self,
        store_dir: str | Path,
        unit_ids: set[str] | None = None,
        reset: bool = True,
    ) -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.unit_ids = list(unit_ids) if unit_ids is not None else None
        if reset:
            self.backend = InMemoryMemoryBackend()

    def ingest(self, documents: list[Document]) -> None:
        for document in documents:
            self.backend.write(
                session_id=document.user_id or "__default__",
                text=document.content,
                metadata={
                    "amb_document_id": document.id,
                    "user_id": document.user_id,
                    "messages": document.messages,
                    "timestamp": document.timestamp,
                    "context": document.context,
                },
            )

    def retrieve(
        self,
        query: str,
        k: int = 10,
        user_id: str | None = None,
        query_timestamp: str | None = None,
    ) -> tuple[list[Document], dict[str, Any]]:
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
        documents = [
            Document(
                id=str(record.metadata.get("amb_document_id", record.id)),
                content=record.text,
                user_id=record.metadata.get("user_id"),
                messages=record.metadata.get("messages"),
                timestamp=record.metadata.get("timestamp"),
                context=record.metadata.get("context"),
            )
            for record in records
        ]
        raw_response = {
            "memory_provider": self.memory_provider,
            "mode": self.mode,
            "query": query,
            "k": k,
            "user_id": user_id,
            "query_timestamp": query_timestamp,
            "returned": len(documents),
            "retrieved_ids": [document.id for document in documents],
        }
        return documents, raw_response

    def direct_answer(
        self,
        query: str,
        user_id: str | None = None,
        query_timestamp: str | None = None,
    ) -> tuple[str, str, dict[str, Any]]:
        documents, raw_response = self.retrieve(
            query,
            k=10,
            user_id=user_id,
            query_timestamp=query_timestamp,
        )
        context_text = "\n".join(document.content for document in documents)
        answer = documents[0].content if documents else ""
        raw_response = {
            **raw_response,
            "answer_strategy": "first_retrieved_document",
            "context_tokens": len(context_text.split()),
        }
        return answer, context_text, raw_response
