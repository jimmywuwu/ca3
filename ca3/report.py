from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    metrics: dict[str, float]
    cases: list[dict[str, Any]]
    passed: bool


def result_to_dict(result: BenchmarkResult) -> dict[str, Any]:
    return asdict(result)


def report_to_dict(results: list[BenchmarkResult]) -> dict[str, Any]:
    return {
        "overall_pass": all(result.passed for result in results),
        "benchmarks": [result_to_dict(result) for result in results],
    }


def run_all_smokes() -> dict[str, Any]:
    from ca3.benchmarks import run_amb_smoke, run_memoryarena_smoke, run_statebench_smoke

    return report_to_dict([
        run_memoryarena_smoke(),
        run_statebench_smoke(),
        run_amb_smoke(),
    ])


def write_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path
