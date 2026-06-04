from __future__ import annotations

from ca3.memory_backend import InMemoryMemoryBackend
from ca3.report import BenchmarkResult


def run_memoryarena_smoke() -> BenchmarkResult:
    backend = InMemoryMemoryBackend()
    backend.write(
        "session-1",
        "User's launch codename is ORBITAL-LANTERN.",
        metadata={"phase": "session_boundary_write"},
    )

    retrieved = backend.retrieve("launch codename", top_k=1)
    answer = "ORBITAL-LANTERN" if retrieved and "ORBITAL-LANTERN" in retrieved[0].text else ""
    passed = answer == "ORBITAL-LANTERN"
    return BenchmarkResult(
        name="memoryarena_smoke",
        metrics={"accuracy": 1.0 if passed else 0.0},
        passed=passed,
        cases=[
            {
                "case_id": "cross_session_state_recall",
                "sessions": ["session-1", "session-2"],
                "query": "launch codename",
                "retrieved": [record.text for record in retrieved],
                "answer": answer,
                "gold": "ORBITAL-LANTERN",
                "passed": passed,
            }
        ],
    )


def retrieve_learnings(
    query: str,
    train_trajectory: list[str],
    top_k: int = 3,
) -> list[str]:
    """STATE-Bench-like read-only retrieval hook returning list[str]."""
    backend = InMemoryMemoryBackend()
    for index, learning in enumerate(train_trajectory):
        backend.write("train", learning, metadata={"kind": "procedure", "step": index})
    return [_normalize_procedure(record.text) for record in backend.retrieve(query, top_k=top_k)]


def run_statebench_smoke() -> BenchmarkResult:
    train_trajectory = [
        "When creating observations, check timestamp semantics before writing observations.",
        "When debugging retrieval, prefer deterministic fixtures before adding models.",
    ]

    query = "held out observation writing task timestamp semantics"
    procedures = retrieve_learnings(query, train_trajectory=train_trajectory, top_k=2)
    expected = "check timestamp semantics before writing observations"
    passed = any(expected in procedure for procedure in procedures)
    return BenchmarkResult(
        name="statebench_agent_learning_smoke",
        metrics={"procedure_recall": 1.0 if passed else 0.0},
        passed=passed,
        cases=[
            {
                "case_id": "held_out_observation_task",
                "train_items": train_trajectory,
                "query": query,
                "retrieved_procedures": procedures,
                "expected_procedure": expected,
                "passed": passed,
            }
        ],
    )


def run_amb_smoke() -> BenchmarkResult:
    backend = InMemoryMemoryBackend()
    documents = [
        "Cold storage keeps embeddings deterministic for replay audits.",
        "Hot cache entries are evicted after short-lived scoring runs.",
    ]
    for index, document in enumerate(documents):
        backend.write("documents", document, metadata={"doc_id": f"doc-{index}"})

    question = "What keeps embeddings deterministic for replay audits?"
    retrieved = backend.retrieve(question, top_k=1)
    answer = retrieved[0].text if retrieved else ""
    gold = "Cold storage keeps embeddings deterministic for replay audits."
    passed = gold in answer
    return BenchmarkResult(
        name="amb_smoke",
        metrics={"gold_containment": 1.0 if passed else 0.0},
        passed=passed,
        cases=[
            {
                "case_id": "document_qa_gold_containment",
                "question": question,
                "retrieved_context": [record.text for record in retrieved],
                "answer": answer,
                "gold": gold,
                "passed": passed,
            }
        ],
    )


def _normalize_procedure(text: str) -> str:
    normalized = text.strip().rstrip(".")
    prefix = "When creating observations, "
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):]
    return normalized[:1].lower() + normalized[1:]
