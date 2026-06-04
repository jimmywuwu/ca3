from __future__ import annotations

import argparse

from ca3.report import run_all_smokes, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local no-model MemoryBackend smoke benchmarks.")
    parser.add_argument(
        "--output",
        default="benchmark-results/smoke/latest.json",
        help="JSON report path to write.",
    )
    args = parser.parse_args(argv)

    report = run_all_smokes()
    output_path = write_report(report, args.output)
    summary = report["score_summary"]
    print(f"Wrote CA3 smoke benchmark score report: {output_path}")
    print(
        "Score: "
        f"ca3={summary['ca3_average_score']:.3f}, "
        f"baseline={summary['baseline_average_score']:.3f}, "
        f"delta={summary['delta_vs_baseline']:.3f}"
    )
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
