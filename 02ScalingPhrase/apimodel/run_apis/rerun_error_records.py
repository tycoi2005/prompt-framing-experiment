#!/usr/bin/env python3
"""Rerun only API/parser/empty-response error records from prior JSONL results."""

from __future__ import annotations

import argparse
import json
import multiprocessing
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


def should_retry(row: dict[str, Any], include_failed: bool) -> bool:
    error = str(row.get("error") or "")
    response_text = str(row.get("response_text") or "")
    eval_result = row.get("eval_result") or {}
    stderr = str(eval_result.get("stderr") or "")
    errors = " ".join(str(item) for item in eval_result.get("errors", []) or [])

    if error:
        return True
    if not response_text.strip():
        return True
    if "leading zeros in decimal integer literals" in stderr + errors:
        return True
    if include_failed and not row.get("passed"):
        return True
    return False


def rows_for_retry(
    dataset_name: str,
    csv_rows: list[dict[str, str]],
    result_path: Path,
    include_failed: bool,
    source_label: str | None = None,
) -> list[dict[str, str]]:
    by_key = latest_by_key(load_jsonl(result_path))
    retry_keys = {
        key
        for key, row in by_key.items()
        if key and key != "None" and should_retry(row, include_failed)
    }
    selected: list[dict[str, str]] = []
    for index, row in enumerate(csv_rows, start=1):
        if runner.row_key(row) in retry_keys:
            selected.append(row | {"_row_number": str(index)})
    label = source_label or result_path.name
    print(
        f"[{dataset_name}] {label}: selected {len(selected)} retry rows "
        f"from {len(by_key)} prior rows"
    )
    return selected


def resolve_source_result_path(
    source_dir: Path,
    dataset_name: str,
    source_model_label: str,
) -> tuple[Path, str]:
    """Resolve the source results JSONL path, supporting merged/ layouts."""
    slug = runner.slugify(source_model_label)
    default_path = source_dir / dataset_name / f"{slug}.{dataset_name}.jsonl"
    if default_path.exists():
        return default_path, default_path.name

    merged_path = source_dir / f"{slug}.merged.{dataset_name}.jsonl"
    if merged_path.exists():
        return merged_path, merged_path.name

    matches = sorted(source_dir.glob(f"**/{slug}*.{dataset_name}.jsonl"))
    if matches:
        return matches[0], matches[0].name
    return default_path, default_path.name


def split_round_robin(rows: list[dict[str, str]], shard_count: int) -> list[list[dict[str, str]]]:
    shards: list[list[dict[str, str]]] = [[] for _ in range(shard_count)]
    for index, row in enumerate(rows):
        shards[index % shard_count].append(row)
    return shards


def single_token_model_cfg(
    model_cfg: dict[str, Any],
    token: str,
    token_index: int,
) -> dict[str, Any]:
    model_label = str(model_cfg.get("name") or model_cfg["model_name"])
    cfg = dict(model_cfg)
    cfg["name"] = f"{model_label}-token{token_index}"
    cfg["token"] = token
    cfg["tokens"] = []
    return cfg


def run_parallel_token_shards(
    dataset_name: str,
    selected_rows: list[dict[str, str]],
    model_cfg: dict[str, Any],
    results_dir: Path,
    timeout_seconds: int,
    eval_timeout_seconds: int,
) -> None:
    tokens = runner.available_tokens(model_cfg)
    if len(tokens) <= 1:
        runner.run_dataset(
            dataset_name=dataset_name,
            rows=selected_rows,
            model_cfg=model_cfg,
            results_dir=results_dir,
            timeout_seconds=timeout_seconds,
            eval_timeout_seconds=eval_timeout_seconds,
            force=True,
        )
        return

    shards = split_round_robin(selected_rows, len(tokens))
    processes: list[multiprocessing.Process] = []
    model_label = str(model_cfg.get("name") or model_cfg["model_name"])
    for token_index, (token, shard_rows) in enumerate(zip(tokens, shards)):
        if not shard_rows:
            continue
        shard_cfg = single_token_model_cfg(model_cfg, token, token_index)
        print(
            f"[{dataset_name}][{model_label}] launching token shard {token_index} "
            f"with {len(shard_rows)} rows",
            flush=True,
        )
        process = multiprocessing.Process(
            target=runner.run_dataset,
            kwargs={
                "dataset_name": dataset_name,
                "rows": shard_rows,
                "model_cfg": shard_cfg,
                "results_dir": results_dir,
                "timeout_seconds": timeout_seconds,
                "eval_timeout_seconds": eval_timeout_seconds,
                "force": True,
            },
        )
        process.start()
        processes.append(process)

    failed = 0
    for process in processes:
        process.join()
        if process.exitcode != 0:
            failed += 1
    if failed:
        raise RuntimeError(f"{failed} token shard worker(s) failed for {dataset_name}/{model_label}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rerun error records from prior API results.")
    parser.add_argument("--config", type=Path, default=runner.DEFAULT_CONFIG_PATH)
    parser.add_argument("--source-results-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, default=SCRIPT_DIR / "results_retry")
    parser.add_argument("--python-csv", type=Path, default=runner.DEFAULT_PYTHON_CSV)
    parser.add_argument("--math-csv", type=Path, default=runner.DEFAULT_MATH_CSV)
    parser.add_argument(
        "--dataset",
        choices=["python", "math", "both"],
        default="both",
        help="Which prior result dataset to retry.",
    )
    parser.add_argument("--model", help="Run one model by config name or model_name.")
    parser.add_argument(
        "--source-model",
        help=(
            "Read retry row keys from this prior result model name, while writing "
            "new outputs under --model. Useful for rerunning one model's errors "
            "with another endpoint/config."
        ),
    )
    parser.add_argument(
        "--include-failed",
        action="store_true",
        help="Also rerun wrong-answer/test-failure rows, not only API/parser/empty rows.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--eval-timeout", type=int, default=10)
    parser.add_argument(
        "--parallel-tokens",
        action="store_true",
        help=(
            "Split selected rows across token + tokens[] for each model and run "
            "one worker per token. Output files are suffixed with -tokenN."
        ),
    )
    parser.add_argument(
        "--shard-count",
        type=int,
        default=1,
        help="Split selected retry rows into this many shards.",
    )
    parser.add_argument(
        "--shard-index",
        type=int,
        default=0,
        help="Run only this zero-based shard index from selected retry rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = runner.load_json(args.config)
    models = config.get("models", [])
    if args.model:
        models = [
            model
            for model in models
            if args.model in {model.get("name"), model.get("model_name")}
        ]
    if not models:
        raise SystemExit("No models selected. Check .env.json or --model.")
    if args.shard_count < 1:
        raise SystemExit("--shard-count must be >= 1.")
    if not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("--shard-index must satisfy 0 <= index < shard-count.")

    source_root = args.source_results_dir
    merged_hint = list(source_root.glob("*.merged.*.jsonl"))
    if not merged_hint:
        merged_hint = list(source_root.glob("**/*.merged.*.jsonl"))

    datasets: list[tuple[str, Path, Path]] = []
    if args.dataset in {"python", "both"}:
        dataset_source = source_root if merged_hint else args.source_results_dir / "python"
        datasets.append(("python", args.python_csv, dataset_source))
    if args.dataset in {"math", "both"}:
        dataset_source = source_root if merged_hint else args.source_results_dir / "math"
        datasets.append(("math", args.math_csv, dataset_source))

    for dataset_name, csv_path, source_dir in datasets:
        csv_rows = runner.load_csv(csv_path)
        for model_cfg in models:
            model_label = str(model_cfg.get("name") or model_cfg["model_name"])
            source_model_label = args.source_model or model_label
            result_path, source_label = resolve_source_result_path(
                source_dir=source_dir,
                dataset_name=dataset_name,
                source_model_label=source_model_label,
            )
            selected_rows = rows_for_retry(
                dataset_name=dataset_name,
                csv_rows=csv_rows,
                result_path=result_path,
                include_failed=args.include_failed,
                source_label=source_label,
            )
            if args.shard_count > 1:
                selected_rows = [
                    row
                    for index, row in enumerate(selected_rows)
                    if index % args.shard_count == args.shard_index
                ]
                print(
                    f"[{dataset_name}][{model_label}] shard "
                    f"{args.shard_index + 1}/{args.shard_count}: "
                    f"{len(selected_rows)} rows",
                    flush=True,
                )
            if not selected_rows:
                continue
            if args.parallel_tokens:
                run_parallel_token_shards(
                    dataset_name=dataset_name,
                    selected_rows=selected_rows,
                    model_cfg=model_cfg,
                    results_dir=args.results_dir,
                    timeout_seconds=args.timeout,
                    eval_timeout_seconds=args.eval_timeout,
                )
            else:
                runner.run_dataset(
                    dataset_name=dataset_name,
                    rows=selected_rows,
                    model_cfg=model_cfg,
                    results_dir=args.results_dir,
                    timeout_seconds=args.timeout,
                    eval_timeout_seconds=args.eval_timeout,
                    force=True,
                )


if __name__ == "__main__":
    main()
