#!/usr/bin/env python3
"""Probe Gemini for current 503 / quota availability.

The script prefers rows that previously failed with 503 / 429 from merged or
retry JSONL files. If no such rows are found, it falls back to a small live
canary sample from the CSVs so the model can still be checked "now".
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import run_api_matrix as runner


SCRIPT_DIR = Path(__file__).resolve().parent


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def latest_by_key(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        latest[str(row.get("row_key"))] = row
    return latest


def is_availability_error(row: dict[str, Any]) -> bool:
    error = str(row.get("error") or "")
    eval_result = row.get("eval_result") or {}
    stderr = str(eval_result.get("stderr") or "")
    quota_errors = " ".join(str(item) for item in row.get("quota_errors", []) or [])
    haystack = " ".join([error, stderr, quota_errors]).lower()
    return any(
        marker in haystack
        for marker in (
            "http 503",
            '"code": 503',
            "unavailable",
            "high demand",
            "http 429",
            "resource_exhausted",
            "quota",
            "rate limit",
            "rate-limit",
        )
    )


def resolve_source_path(source_results_dir: Path, model_label: str, dataset_name: str) -> Path | None:
    slug = runner.slugify(model_label)
    candidates = [
        source_results_dir / f"{slug}.merged.{dataset_name}.jsonl",
        source_results_dir / f"{slug}.{dataset_name}.jsonl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = sorted(source_results_dir.glob(f"**/{slug}*.{dataset_name}.jsonl"))
    return matches[0] if matches else None


def select_probe_rows(
    csv_rows: list[dict[str, str]],
    source_path: Path | None,
    limit: int,
) -> tuple[list[dict[str, str]], str]:
    if source_path is not None:
        latest = latest_by_key(load_jsonl(source_path))
        retry_keys = {key for key, row in latest.items() if key and key != "None" and is_availability_error(row)}
        selected = [row | {"_row_number": str(index)} for index, row in enumerate(csv_rows, start=1) if runner.row_key(row) in retry_keys]
        if selected:
            return selected[:limit], f"source availability failures from {source_path.name}"
    selected = [row | {"_row_number": str(index)} for index, row in enumerate(csv_rows, start=1)][:limit]
    return selected, "live canary sample from CSV (no availability failures found in source)"


def summarize_result_file(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in load_jsonl(path):
        if row.get("passed"):
            counts["passed"] += 1
            continue
        error = str(row.get("error") or "")
        eval_result = row.get("eval_result") or {}
        stderr = str(eval_result.get("stderr") or "")
        quota_errors = " ".join(str(item) for item in row.get("quota_errors", []) or [])
        haystack = " ".join([error, stderr, quota_errors]).lower()
        if any(marker in haystack for marker in ("http 503", '"code": 503', "unavailable", "high demand")):
            counts["http_503"] += 1
        elif any(marker in haystack for marker in ("http 429", "resource_exhausted", "quota", "rate limit", "rate-limit")):
            counts["quota_429"] += 1
        elif error or stderr:
            counts["other_error"] += 1
        else:
            counts["wrong_answer"] += 1
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe Gemini availability and 503 behavior.")
    parser.add_argument("--config", type=Path, default=runner.DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--source-results-dir",
        type=Path,
        help="Directory containing merged/retry JSONL files to mine for prior 503 / 429 rows.",
    )
    parser.add_argument("--results-dir", type=Path, default=SCRIPT_DIR / "results_probe")
    parser.add_argument("--python-csv", type=Path, default=runner.DEFAULT_PYTHON_CSV)
    parser.add_argument("--math-csv", type=Path, default=runner.DEFAULT_MATH_CSV)
    parser.add_argument(
        "--dataset",
        choices=["python", "math", "both"],
        default="both",
        help="Which CSV to probe.",
    )
    parser.add_argument(
        "--model",
        default="gemini-flash",
        help="Model config name or model_name to probe.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows per dataset to probe.")
    parser.add_argument("--timeout", type=int, default=120, help="API timeout seconds.")
    parser.add_argument("--eval-timeout", type=int, default=10, help="Python eval timeout seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = runner.load_json(args.config)
    models = [
        model
        for model in config.get("models", [])
        if args.model in {model.get("name"), model.get("model_name")}
    ]
    if not models:
        raise SystemExit("No Gemini model selected. Check --model or .env.json.")
    model_cfg = models[0]
    model_label = str(model_cfg.get("name") or model_cfg["model_name"])

    datasets: list[tuple[str, Path]] = []
    if args.dataset in {"python", "both"}:
        datasets.append(("python", args.python_csv))
    if args.dataset in {"math", "both"}:
        datasets.append(("math", args.math_csv))

    for dataset_name, csv_path in datasets:
        csv_rows = runner.load_csv(csv_path)
        source_path = None
        if args.source_results_dir:
            source_path = resolve_source_path(args.source_results_dir, model_label, dataset_name)
        selected_rows, selection_reason = select_probe_rows(csv_rows, source_path, args.limit)
        if not selected_rows:
            print(f"[{dataset_name}] no rows selected")
            continue

        print(f"[{dataset_name}] probing {len(selected_rows)} row(s) using {selection_reason}", flush=True)
        output_path = args.results_dir / dataset_name / f"{runner.slugify(model_label)}.{dataset_name}.jsonl"
        if output_path.exists():
            output_path.unlink()
        runner.run_dataset(
            dataset_name=dataset_name,
            rows=selected_rows,
            model_cfg=model_cfg,
            results_dir=args.results_dir,
            timeout_seconds=args.timeout,
            eval_timeout_seconds=args.eval_timeout,
            force=True,
        )

        counts = summarize_result_file(output_path)
        total = sum(counts.values())
        print(
            f"[{dataset_name}] probe summary: total={total}, passed={counts['passed']}, "
            f"http_503={counts['http_503']}, quota_429={counts['quota_429']}, "
            f"other_error={counts['other_error']}, wrong_answer={counts['wrong_answer']}",
            flush=True,
        )


if __name__ == "__main__":
    main()