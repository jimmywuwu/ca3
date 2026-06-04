import json
import subprocess
import sys
from pathlib import Path

from ca3.benchmarks.amb_local import run_amb_local_fixture
from ca3.integrations.amb import Ca3AMBMemoryProvider, Document


def test_amb_provider_retrieve_isolates_user_namespaces(tmp_path):
    provider = Ca3AMBMemoryProvider()
    provider.prepare(tmp_path, reset=True)
    provider.ingest([
        Document(id="alice-secret", content="The launch codename is ORBITAL-LANTERN.", user_id="alice"),
        Document(id="bob-secret", content="The launch codename is COPPER-RIVER.", user_id="bob"),
    ])

    alice_docs, raw = provider.retrieve("launch codename", k=5, user_id="alice")

    assert [doc.id for doc in alice_docs] == ["alice-secret"]
    assert raw["memory_provider"] == "ca3-local"
    assert raw["user_id"] == "alice"
    assert raw["returned"] == 1


def test_amb_provider_direct_answer_returns_omb_compatible_shape(tmp_path):
    provider = Ca3AMBMemoryProvider()
    provider.prepare(tmp_path, reset=True)
    provider.ingest([
        Document(id="doc-1", content="Mira prefers green tea before reviews.", user_id="mira"),
    ])

    answer, context_text, raw = provider.direct_answer("What does Mira prefer before reviews?", user_id="mira")

    assert answer == "Mira prefers green tea before reviews."
    assert context_text == "Mira prefers green tea before reviews."
    assert raw["mode"] == "local/no-model"
    assert raw["retrieved_ids"] == ["doc-1"]


def test_amb_local_fixture_report_contains_scores_baseline_and_per_query_results():
    report = run_amb_local_fixture()

    assert report["memory_provider"] == "ca3-local"
    assert report["mode"] == "agent"
    assert report["scoring_mode"] == "local/no-model"
    assert report["benchmark_family"] == "agent-memory-benchmark"
    assert report["official_leaderboard"] is False
    assert report["dataset"] == "amb_local_fixture"
    assert report["total_queries"] >= 3
    assert report["correct"] == report["total_queries"]
    assert report["accuracy"] == 1.0
    assert report["no_memory_baseline"]["accuracy"] == 0.0
    assert report["delta_vs_baseline"] == 1.0
    assert report["avg_retrieve_time_ms"] >= 0.0
    assert report["avg_context_tokens"] > 0.0
    assert len({item["user_id"] for item in report["per_query"]}) >= 2
    assert all(item["passed"] is True for item in report["per_query"])
    assert all(item["judge"] in {"exact", "gold_containment"} for item in report["per_query"])


def test_amb_local_cli_writes_json_report(tmp_path):
    output_path = tmp_path / "amb-local-report.json"

    completed = subprocess.run(
        [sys.executable, "-m", "ca3.benchmarks.amb_local", "--output", str(output_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert str(output_path) in completed.stdout
    report = json.loads(output_path.read_text())
    assert report["dataset"] == "amb_local_fixture"
    assert report["memory_provider"] == "ca3-local"
    assert report["mode"] == "agent"
    assert report["accuracy"] == 1.0
    assert report["no_memory_baseline"]["total_queries"] == report["total_queries"]
    assert report["delta_vs_baseline"] == 1.0
