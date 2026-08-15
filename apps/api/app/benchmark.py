import argparse
import json
from pathlib import Path

from app.schemas.issue import IssueIntakeRequest
from app.services.agent_service import create_run


def run_benchmark(cases_path: Path, output_path: Path) -> dict[str, object]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    for case in cases:
        try:
            run = create_run(IssueIntakeRequest(issue_url=case["issue_url"]))
            prefixes = tuple(case.get("expected_path_prefixes", []))
            touched_expected_area = any(path.startswith(prefixes) for path in run.report.patch_application.changed_files)
            result = {
                "name": case["name"], "run_id": str(run.id), "status": run.status,
                "baseline_failed": run.report.verification.baseline_failed,
                "verification_passed": run.report.verification.status == "passed",
                "runtime_matched": run.workspace.sandbox.runtime == case["expected_runtime"],
                "touched_expected_area": touched_expected_area,
            }
        except Exception as error:
            result = {"name": case["name"], "status": "error", "error": str(error)[:500]}
        results.append(result)
    passed = sum(item.get("verification_passed") is True for item in results)
    report = {"cases": results, "verified_fixes": passed, "total": len(results), "pass_rate": passed / len(results) if results else 0}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate IssuePilot against the curated issue benchmark")
    parser.add_argument("--cases", type=Path, default=Path("../../benchmarks/issues.json"))
    parser.add_argument("--output", type=Path, default=Path("../../benchmarks/results/latest.json"))
    args = parser.parse_args()
    print(json.dumps(run_benchmark(args.cases, args.output), indent=2))


if __name__ == "__main__":
    main()
