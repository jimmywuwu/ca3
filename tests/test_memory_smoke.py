import json
import subprocess
import sys
from pathlib import Path

from ca3.benchmarks import retrieve_learnings, run_amb_smoke, run_memoryarena_smoke, run_statebench_smoke
from ca3.memory_backend import InMemoryMemoryBackend
from ca3.report import run_all_smokes, write_report


def test_memory_backend_retrieves_lexically_relevant_records_in_score_order():
    backend = InMemoryMemoryBackend()
    backend.write("session-1", "alice likes green tea", metadata={"kind": "preference"})
    backend.write("session-2", "bob likes espresso", metadata={"kind": "preference"})
    backend.write("session-3", "alice moved to Kyoto", metadata={"kind": "profile"})

    hits = backend.retrieve("what city did alice move to", top_k=2)

    assert [hit.text for hit in hits] == ["alice moved to Kyoto", "alice likes green tea"]
    assert hits[0].metadata == {"kind": "profile"}


def test_memoryarena_smoke_uses_previous_session_state_to_answer_later_session():
    result = run_memoryarena_smoke()

    assert result.name == "memoryarena_smoke"
    assert result.metrics["accuracy"] == 1.0
    assert result.passed is True
    assert result.cases[0]["retrieved"] == ["User's launch codename is ORBITAL-LANTERN."]
    assert result.cases[0]["answer"] == "ORBITAL-LANTERN"


def test_statebench_retrieve_learnings_api_returns_top_k_list_of_strings():
    train_trajectory = [
        "When creating observations, check timestamp semantics before writing observations.",
        "When debugging retrieval, prefer deterministic fixtures before adding models.",
    ]

    learnings = retrieve_learnings(
        "held out observation writing task timestamp semantics",
        train_trajectory=train_trajectory,
        top_k=1,
    )

    assert learnings == ["check timestamp semantics before writing observations"]


def test_statebench_smoke_retrieves_expected_procedure_for_held_out_task():
    result = run_statebench_smoke()

    assert result.name == "statebench_agent_learning_smoke"
    assert result.metrics["procedure_recall"] == 1.0
    assert result.passed is True
    assert "check timestamp semantics before writing observations" in result.cases[0]["retrieved_procedures"]


def test_amb_smoke_answers_from_retrieved_document_context_with_gold_containment():
    result = run_amb_smoke()

    assert result.name == "amb_smoke"
    assert result.metrics["gold_containment"] == 1.0
    assert result.passed is True
    assert result.cases[0]["answer"] == "Cold storage keeps embeddings deterministic for replay audits."


def test_run_all_smokes_returns_serializable_report_with_overall_pass(tmp_path):
    report = run_all_smokes()
    output_path = tmp_path / "report.json"

    write_report(report, output_path)
    loaded = json.loads(output_path.read_text())

    assert loaded["overall_pass"] is True
    assert [item["name"] for item in loaded["benchmarks"]] == [
        "memoryarena_smoke",
        "statebench_agent_learning_smoke",
        "amb_smoke",
    ]
    assert loaded["benchmarks"][0]["cases"][0]["passed"] is True


def test_cli_writes_json_report(tmp_path):
    output_path = tmp_path / "ca3-smoke-report.json"

    completed = subprocess.run(
        [sys.executable, "-m", "ca3.benchmarks.smoke", "--output", str(output_path)],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert str(output_path) in completed.stdout
    report = json.loads(output_path.read_text())
    assert report["overall_pass"] is True
    assert {bench["name"] for bench in report["benchmarks"]} == {
        "memoryarena_smoke",
        "statebench_agent_learning_smoke",
        "amb_smoke",
    }
