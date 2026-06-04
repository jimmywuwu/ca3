from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from time import perf_counter
from typing import Any

from ca3.integrations.amb import Ca3AMBMemoryProvider, Document, EvalSummary, Query, QueryResult


FIXTURE_DOCUMENTS = [
    Document(
        id="mira-review-tea",
        content="Mira prefers green tea before reviews.",
        user_id="mira",
        timestamp="2026-01-01T09:00:00Z",
    ),
    Document(
        id="mira-db-window",
        content="Mira schedules database maintenance on Tuesday nights.",
        user_id="mira",
        timestamp="2026-01-02T09:00:00Z",
    ),
    Document(
        id="noah-deploy-check",
        content="Noah requires checksum verification before deploys.",
        user_id="noah",
        timestamp="2026-01-01T10:00:00Z",
    ),
    Document(
        id="noah-cache-policy",
        content="Noah keeps hot cache TTL at fifteen minutes.",
        user_id="noah",
        timestamp="2026-01-02T10:00:00Z",
    ),
]

FIXTURE_QUERIES = [
    Query(
        id="mira_review_preference",
        query="What does Mira prefer before reviews?",
        gold="Mira prefers green tea before reviews.",
        user_id="mira",
        k=3,
        judge="exact",
    ),
    Query(
        id="mira_maintenance_window",
        query="When does Mira schedule database maintenance?",
        gold="Tuesday nights",
        user_id="mira",
        k=3,
        judge="gold_containment",
    ),
    Query(
        id="noah_deploy_requirement",
        query="What verification does Noah require before deploys?",
        gold="checksum verification",
        user_id="noah",
        k=3,
        judge="gold_containment",
    ),
    Query(
        id="noah_cache_ttl",
        query="What hot cache TTL does Noah keep?",
        gold="Noah keeps hot cache TTL at fifteen minutes.",
        user_id="noah",
        k=3,
        judge="exact",
    ),
]


def run_amb_local_fixture(store_dir: str | Path | None = None) -> dict[str, Any]:
    if store_dir is None:
        with tempfile.TemporaryDirectory(prefix="ca3-amb-local-") as temporary_store:
            return _run_amb_local_fixture(Path(temporary_store))
    return _run_amb_local_fixture(Path(store_dir))


def _run_amb_local_fixture(store_dir: Path) -> dict[str, Any]:
    provider = Ca3AMBMemoryProvider()
    provider.prepare(store_dir, reset=True)
    provider.ingest(FIXTURE_DOCUMENTS)

    per_query: list[QueryResult] = []
    for query in FIXTURE_QUERIES:
        started = perf_counter()
        retrieved, _retrieve_raw = provider.retrieve(
            query.query,
            k=query.k,
            user_id=query.user_id,
            query_timestamp=query.query_timestamp,
        )
        retrieve_time_ms = (perf_counter() - started) * 1000.0
        answer, context_text, raw_answer = provider.direct_answer(
            query.query,
            user_id=query.user_id,
            query_timestamp=query.query_timestamp,
        )
        passed = judge_answer(answer, query.gold, query.judge)
        per_query.append(
            QueryResult(
                query_id=query.id,
                query=query.query,
                user_id=query.user_id,
                gold=query.gold,
                answer=answer,
                context_text=context_text,
                retrieved_ids=[document.id for document in retrieved] or raw_answer.get("retrieved_ids", []),
                passed=passed,
                judge=query.judge,
                retrieve_time_ms=retrieve_time_ms,
                context_tokens=len(context_text.split()),
                baseline_answer="",
                baseline_passed=judge_answer("", query.gold, query.judge),
            )
        )

    total = len(per_query)
    correct = sum(1 for result in per_query if result.passed)
    baseline_correct = sum(1 for result in per_query if result.baseline_passed)
    accuracy = correct / total if total else 0.0
    baseline_accuracy = baseline_correct / total if total else 0.0
    summary = EvalSummary(
        total_queries=total,
        correct=correct,
        accuracy=accuracy,
        avg_retrieve_time_ms=sum(result.retrieve_time_ms for result in per_query) / total if total else 0.0,
        avg_context_tokens=sum(result.context_tokens for result in per_query) / total if total else 0.0,
        per_query=per_query,
        no_memory_baseline={
            "total_queries": total,
            "correct": baseline_correct,
            "accuracy": baseline_accuracy,
            "answer_strategy": "empty_no_memory_answer",
        },
        delta_vs_baseline=accuracy - baseline_accuracy,
    )
    return summary.to_dict()


def judge_answer(answer: str, gold: str, judge: str) -> bool:
    normalized_answer = _normalize(answer)
    normalized_gold = _normalize(gold)
    if judge == "exact":
        return normalized_answer == normalized_gold
    if judge == "gold_containment":
        return normalized_gold in normalized_answer
    raise ValueError(f"Unsupported local AMB judge: {judge}")


def write_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AMB-compatible local fixture scoring without external models or APIs."
    )
    parser.add_argument(
        "--output",
        default="benchmark-results/amb-local/latest.json",
        help="JSON report path to write.",
    )
    parser.add_argument(
        "--store-dir",
        default=".amb-local-store",
        help="Local provider store directory for OMB-compatible prepare().",
    )
    args = parser.parse_args(argv)

    report = run_amb_local_fixture(store_dir=args.store_dir)
    output_path = write_report(report, args.output)
    print(f"Wrote CA3 AMB-compatible local/no-model score report: {output_path}")
    print(
        "Score: "
        f"ca3={report['accuracy']:.3f}, "
        f"baseline={report['no_memory_baseline']['accuracy']:.3f}, "
        f"delta={report['delta_vs_baseline']:.3f}"
    )
    return 0 if report["accuracy"] >= report["no_memory_baseline"]["accuracy"] else 1


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


if __name__ == "__main__":
    raise SystemExit(main())
