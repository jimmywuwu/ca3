from __future__ import annotations

from pathlib import Path

from ca3.benchmarks.amb_provider import Ca3OpenMemoryBenchmarkProvider, records_to_omb_documents
from ca3.benchmarks.install_omb_provider import install_provider


class FakeDocument:
    def __init__(self, id: str, content: str, user_id: str | None = None, timestamp: str | None = None, context: str | None = None, messages=None):
        self.id = id
        self.content = content
        self.user_id = user_id
        self.timestamp = timestamp
        self.context = context
        self.messages = messages


def test_ca3_omb_provider_retrieves_user_scoped_documents(tmp_path):
    provider = Ca3OpenMemoryBenchmarkProvider()
    provider.prepare(tmp_path, unit_ids={"alice", "bob"}, reset=True)
    provider.ingest([
        FakeDocument("alice-1", "Alice prefers green tea before incident reviews.", user_id="alice"),
        FakeDocument("bob-1", "Bob prefers espresso before incident reviews.", user_id="bob"),
    ])

    records, raw = provider.retrieve("incident reviews green tea", k=5, user_id="alice")

    assert [record.metadata["omb_document_id"] for record in records] == ["alice-1"]
    assert raw["memory_provider"] == "ca3"
    assert raw["user_id"] == "alice"
    assert raw["returned"] == 1


def test_records_to_omb_documents_preserves_document_shape(tmp_path):
    provider = Ca3OpenMemoryBenchmarkProvider()
    provider.prepare(tmp_path, reset=True)
    provider.ingest([FakeDocument("doc-1", "A durable fact.", user_id="u1", timestamp="2026-01-01T00:00:00Z")])
    records, _ = provider.retrieve("durable fact", user_id="u1")

    docs = records_to_omb_documents(records, FakeDocument)

    assert len(docs) == 1
    assert docs[0].id == "doc-1"
    assert docs[0].content == "A durable fact."
    assert docs[0].user_id == "u1"
    assert docs[0].timestamp == "2026-01-01T00:00:00Z"


def test_install_omb_provider_writes_provider_and_patches_registry(tmp_path):
    omb = tmp_path / "open-memory-benchmark"
    memory_dir = omb / "src" / "memory_bench" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "__init__.py").write_text(
        "from .base import MemoryProvider\n"
        "from .bm25 import BM25MemoryProvider\n"
        "from .supermemory import SupermemoryMemoryProvider\n"
        "\n"
        "REGISTRY: dict[str, type[MemoryProvider]] = {\n"
        "    \"bm25\": BM25MemoryProvider,\n"
        "}\n",
        encoding="utf-8",
    )
    ca3_root = Path(__file__).resolve().parents[1]

    modified = install_provider(omb, ca3_root)

    provider_file = memory_dir / "ca3.py"
    registry = (memory_dir / "__init__.py").read_text(encoding="utf-8")
    assert provider_file in modified
    assert "class Ca3MemoryProvider(MemoryProvider):" in provider_file.read_text(encoding="utf-8")
    assert "from .ca3 import Ca3MemoryProvider" in registry
    assert '    "ca3": Ca3MemoryProvider,' in registry
