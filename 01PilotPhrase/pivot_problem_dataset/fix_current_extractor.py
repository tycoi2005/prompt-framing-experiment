from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import re
import signal
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DEFAULT_RESULTS_DIR = ROOT / "results"
DEFAULT_PROBLEMS_CSV = ROOT / "problems.csv"
EXEC_TIMEOUT_SEC = 10


class ExecTimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise ExecTimeoutError("exec timed out")


def is_python_code(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def extract_python_code(response: str) -> str:
    matches = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
    if matches:
        return matches[-1].strip()
    matches = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
    if matches:
        return matches[-1].strip()
    return response.strip()


def evaluate_code(code: str, test_list: list[str], timeout_sec: int = EXEC_TIMEOUT_SEC) -> dict:
    if not code:
        return {
            "passed": False,
            "tests_passed": 0,
            "tests_total": len(test_list),
            "errors": ["No code extracted"],
        }

    if not is_python_code(code):
        return {
            "passed": False,
            "tests_passed": 0,
            "tests_total": len(test_list),
            "errors": ["Response is not valid Python"],
        }

    passed_count = 0
    errors = []
    for test in test_list:
        namespace = {}
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_sec)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exec(code, namespace, namespace)
                exec(test, namespace, namespace)
            signal.alarm(0)
            passed_count += 1
        except ExecTimeoutError:
            signal.alarm(0)
            errors.append(f"Test timed out (>{timeout_sec}s): {test}")
        except Exception as exc:
            signal.alarm(0)
            errors.append(f"Test failed: {test} | Error: {str(exc)}")

    return {
        "passed": passed_count == len(test_list) and len(test_list) > 0,
        "tests_passed": passed_count,
        "tests_total": len(test_list),
        "errors": errors,
    }


def load_tests(problems_csv: Path) -> dict[str, list[str]]:
    problems = pd.read_csv(problems_csv)
    tests_by_task_id = {}
    for _, row in problems.iterrows():
        standard_tests = json.loads(row.get("test_cases", "[]"))
        challenge_tests = json.loads(row.get("challenge_test_list", "[]"))
        task_id = f"{int(row['task_id'])}_{int(row['category_id'])}"
        tests_by_task_id[task_id] = standard_tests + challenge_tests
    return tests_by_task_id


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path} line {line_no}: {exc}") from exc


def output_path_for(input_path: Path) -> Path:
    if input_path.name.endswith("_final.jsonl"):
        return input_path.with_name(input_path.name.replace("_final.jsonl", "_fixextractor.jsonl"))
    return input_path.with_name(input_path.stem + "_fixextractor.jsonl")


def repair_file(input_path: Path, tests_by_task_id: dict[str, list[str]], timeout_sec: int, reevaluate_all: bool) -> dict:
    output_path = output_path_for(input_path)
    total = 0
    old_passed = 0
    new_passed = 0
    changed_extraction = 0
    changed_pass = 0

    with output_path.open("w", encoding="utf-8") as out:
        for row in iter_jsonl(input_path):
            total += 1
            task_id = row["task_id"]
            test_list = tests_by_task_id.get(task_id)
            if test_list is None:
                raise KeyError(f"No tests found for task_id {task_id!r}")

            old_extracted = row.get("extracted_code") or ""
            new_extracted = extract_python_code(row.get("response_text") or "")
            extraction_changed = old_extracted.strip() != new_extracted.strip()
            if reevaluate_all or extraction_changed:
                eval_res = evaluate_code(new_extracted, test_list, timeout_sec=timeout_sec)
            else:
                eval_res = {
                    "passed": row.get("passed", False),
                    "tests_passed": row.get("tests_passed", 0),
                    "tests_total": row.get("tests_total", len(test_list)),
                    "errors": row.get("errors", []),
                }

            old_passed += int(bool(row.get("passed", False)))
            new_passed += int(bool(eval_res["passed"]))
            changed_extraction += int(extraction_changed)
            changed_pass += int(bool(row.get("passed", False)) != bool(eval_res["passed"]))

            repaired = dict(row)
            repaired.update(
                {
                    "passed": eval_res["passed"],
                    "tests_passed": eval_res["tests_passed"],
                    "tests_total": eval_res["tests_total"],
                    "errors": eval_res["errors"],
                    "extracted_code": new_extracted,
                    "fixextractor_timestamp": datetime.now().isoformat(),
                    "fixextractor_version": "v1_ast_plain_response_fallback",
                    "original_passed": row.get("passed"),
                    "original_tests_passed": row.get("tests_passed"),
                    "original_errors": row.get("errors"),
                    "original_extracted_code_empty": not bool(old_extracted.strip()),
                }
            )
            out.write(json.dumps(repaired, ensure_ascii=False) + "\n")

    return {
        "input": str(input_path),
        "output": str(output_path),
        "total": total,
        "old_passed": old_passed,
        "new_passed": new_passed,
        "changed_extraction": changed_extraction,
        "changed_pass": changed_pass,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-evaluate existing result JSONL files with the fixed extractor.")
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--problems-csv", type=Path, default=DEFAULT_PROBLEMS_CSV)
    parser.add_argument("--timeout-sec", type=int, default=EXEC_TIMEOUT_SEC)
    parser.add_argument("--pattern", default="*_final.jsonl")
    parser.add_argument(
        "--reevaluate-all",
        action="store_true",
        help="Re-run tests for every row. By default only rows whose extracted code changes are re-evaluated.",
    )
    args = parser.parse_args()

    tests_by_task_id = load_tests(args.problems_csv)
    files = sorted(args.results_dir.glob(args.pattern))
    if not files:
        raise FileNotFoundError(f"No files matched {args.results_dir / args.pattern}")

    summaries = [repair_file(path, tests_by_task_id, args.timeout_sec, args.reevaluate_all) for path in files]
    summary_path = args.results_dir / "fixextractor_summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    print(f"Processed {len(files)} file(s).")
    for item in summaries:
        print(
            f"{Path(item['input']).name}: {item['old_passed']}/{item['total']} -> "
            f"{item['new_passed']}/{item['total']} passed; "
            f"changed extraction={item['changed_extraction']}, changed pass={item['changed_pass']}"
        )
        print(f"  output: {item['output']}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
