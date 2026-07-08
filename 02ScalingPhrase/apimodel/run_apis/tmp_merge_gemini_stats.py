#!/usr/bin/env python3
import json
from pathlib import Path

MERGED_DIR = Path(
    "/Users/macos/LearningSpace/ue-courses/Thesis/02ScalingPhrase/apimodel/run_apis/remote_downloads/20260513_172249/merged"
)
RETRY_ROOT = Path(
    "/Users/macos/LearningSpace/ue-courses/Thesis/02ScalingPhrase/apimodel/run_apis/results_retry"
)


def row_key(row: dict) -> str:
    key = row.get("row_key")
    if key:
        return str(key)
    return f"{row.get('task_id')}::{row.get('category_id')}"


def is_newer(row: dict, current: dict | None) -> bool:
    if current is None:
        return True
    return str(row.get("timestamp") or "") >= str(current.get("timestamp") or "")


def main() -> None:
    source_files = list(MERGED_DIR.glob("gemini-flash.merged.*.jsonl"))
    if not source_files:
        raise SystemExit("No merged gemini-flash files found")

    by_key: dict[str, dict] = {}
    for path in source_files:
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = row_key(row)
                if is_newer(row, by_key.get(key)):
                    by_key[key] = row

    retry_files = [
        *RETRY_ROOT.glob("**/gemini-flash-token*.jsonl"),
        *RETRY_ROOT.glob("**/gemini-flash-main-token*.jsonl"),
    ]
    for path in retry_files:
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                key = row_key(row)
                if is_newer(row, by_key.get(key)):
                    by_key[key] = row

    total = 0
    clean = 0
    api_error = 0
    empty_response = 0
    leading_zero_err = 0

    for row in by_key.values():
        total += 1
        error = str(row.get("error") or "")
        response_text = str(row.get("response_text") or "")
        eval_result = row.get("eval_result") or {}
        stderr = str(eval_result.get("stderr") or "")
        errors = " ".join(str(item) for item in (eval_result.get("errors") or []))

        has_api_error = bool(error)
        has_empty = not response_text.strip()
        has_leading_zero = "leading zeros in decimal integer literals" in (
            stderr + errors
        )

        if has_api_error:
            api_error += 1
        if has_empty:
            empty_response += 1
        if has_leading_zero:
            leading_zero_err += 1
        if (not has_api_error) and (not has_empty) and (not has_leading_zero):
            clean += 1

    print(f"total={total}")
    print(f"clean={clean}")
    print(f"api_error={api_error}")
    print(f"empty_response={empty_response}")
    print(f"leading_zero_err={leading_zero_err}")


if __name__ == "__main__":
    main()
