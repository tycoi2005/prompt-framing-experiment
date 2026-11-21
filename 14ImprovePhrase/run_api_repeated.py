#!/usr/bin/env python3
"""Run independent repeated generations (k=3) on the 6 core prompt conditions
for Cloud API models (R1C3 / R2C14 / R2C15).

Core prompt conditions (from the 18-variant factorial matrix):
  1  : neutral    + no role        + plaintext  (baseline)
  2  : neutral    + no role        + json       (format: JSON vs plaintext)
  3  : neutral    + no role        + xml        (format: XML vs plaintext)
  4  : neutral    + expert persona + plaintext  (role: expert vs no role)
  7  : polite     + no role        + plaintext  (tone: polite vs neutral)
  13 : aggressive + no role        + plaintext  (tone: aggressive vs neutral)

50 tasks x 6 conditions x 3 repeats = 900 calls per model-task pair.
Restart-safe: only error-free (task_id, category_id, rep_id) keys are skipped.
Full raw responses are saved for both Python and Math.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RUN_APIS_DIR = REPO_ROOT / "02ScalingPhrase" / "apimodel" / "run_apis"
sys.path.insert(0, str(RUN_APIS_DIR))

from run_api_matrix import (  # noqa: E402
    MATH_SYSTEM_PROMPT,
    PYTHON_SYSTEM_PROMPT,
    ResponseContentError,
    available_tokens,
    call_chat_completion,
    evaluate_math_response,
    evaluate_python_response,
    is_quota_error,
    load_csv,
    load_json,
    mask_token,
    slugify,
)

DEFAULT_CONFIG_PATH = RUN_APIS_DIR / ".env.json"
DEFAULT_PYTHON_CSV = RUN_APIS_DIR / "problems.csv"
DEFAULT_MATH_CSV = RUN_APIS_DIR / "problems.math.csv"
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results_api_repeated"
DEFAULT_LOGS_DIR = SCRIPT_DIR / "logs"

DEFAULT_CORE_CATEGORIES = ["1", "2", "3", "4", "7", "13"]
DEFAULT_STUDY_MODELS = ["deepseek-v4-flash", "gemini-flash"]

CATEGORY_LABELS = {
    "1": "neutral_norole_plaintext",
    "2": "neutral_norole_json",
    "3": "neutral_norole_xml",
    "4": "neutral_role_plaintext",
    "7": "polite_norole_plaintext",
    "13": "aggressive_norole_plaintext",
}

EXIT_QUOTA_EXHAUSTED = 2


def setup_logger(log_dir: Path, log_file: Path | None = None) -> tuple[logging.Logger, Path]:
    log_dir.mkdir(parents=True, exist_ok=True)
    if log_file is None:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"run_api_repeated_{stamp}.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("run_api_repeated")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger, log_file


def repeated_row_key(task_id: str, category_id: str, rep_id: int) -> str:
    return f"{task_id}::{category_id}::rep{rep_id}"


def inspect_progress(path: Path) -> tuple[set[str], set[str], int]:
    """Return (completed_ok_keys, failed_only_keys, total_lines)."""
    ok_keys: set[str] = set()
    err_keys: set[str] = set()
    total_lines = 0
    if not path.exists():
        return ok_keys, err_keys, total_lines
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_lines += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = rec.get("row_key")
            if not key:
                continue
            if rec.get("error") is None:
                ok_keys.add(str(key))
            else:
                err_keys.add(str(key))
    failed_only = err_keys - ok_keys
    return ok_keys, failed_only, total_lines


def compact_jsonl_remove_errors(path: Path, logger: logging.Logger) -> None:
    """Optional cleanup: keep only error-free unique row_keys in the output JSONL."""
    if not path.exists():
        return
    kept: dict[str, str] = {}
    removed = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                removed += 1
                continue
            if rec.get("error") is None and rec.get("row_key"):
                kept[str(rec["row_key"])] = line
            else:
                removed += 1
    if removed > 0:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as out:
            for line in kept.values():
                out.write(line)
        tmp.replace(path)
        logger.info("Cleaned %d error/duplicate lines from %s (%d valid rows kept)", removed, path, len(kept))


def run_repeated_dataset(
    dataset_name: str,
    rows: list[dict[str, str]],
    model_cfg: dict[str, Any],
    results_dir: Path,
    repeats: int,
    timeout_seconds: int,
    eval_timeout_seconds: int,
    max_retries_transient: int,
    quota_wait_seconds: int,
    stop_after_quota_errors: int,
    delay_override: float | None,
    force: bool,
    clean_errors: bool,
    logger: logging.Logger,
) -> tuple[Path, bool]:
    """Run one dataset-model pair. Returns (output_path, stopped_for_quota)."""
    model_label = str(model_cfg.get("name") or model_cfg["model_name"])
    output_dir = results_dir / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slugify(model_label)}.{dataset_name}.repeated.jsonl"
    errors_path = output_dir / f"{slugify(model_label)}.{dataset_name}.errors.jsonl"

    if clean_errors:
        compact_jsonl_remove_errors(output_path, logger)

    ok_keys, failed_only, _ = inspect_progress(output_path)
    completed = set() if force else ok_keys
    delay = float(model_cfg.get("delay_seconds", 2)) if delay_override is None else delay_override
    tokens = available_tokens(model_cfg)
    if not tokens:
        raise ValueError(f"No token configured for model {model_label}")

    # Outer loop by rep_id so rep 1, rep 2, rep 3 are separated in time.
    schedule: list[tuple[int, dict[str, str]]] = [
        (rep_id, row) for rep_id in range(1, repeats + 1) for row in rows
    ]
    total_target = len(schedule)
    remaining = [
        (rep_id, row)
        for rep_id, row in schedule
        if repeated_row_key(row["task_id"], row["category_id"], rep_id) not in completed
    ]
    logger.info(
        "[%s][%s] total=%d | completed_ok=%d | prev_failed_to_retry=%d | remaining=%d | keys=%d | delay=%.1fs",
        dataset_name,
        model_label,
        total_target,
        len(ok_keys),
        len(failed_only),
        len(remaining),
        len(tokens),
        delay,
    )
    if not remaining:
        logger.info("[%s][%s] All %d target rows already completed.", dataset_name, model_label, total_target)
        return output_path, False

    token_cursor = 0
    done_now = 0
    passed_now = 0
    errors_now = 0
    consecutive_quota_failures = 0
    stopped_for_quota = False

    with (
        output_path.open("a", encoding="utf-8") as out,
        errors_path.open("a", encoding="utf-8") as err_out,
    ):
        for rep_id, row in remaining:
            key = repeated_row_key(row["task_id"], row["category_id"], rep_id)
            done_now += 1
            started = time.time()
            token_used = ""
            token_index_used: int | None = None
            quota_errors: list[str] = []
            response_text = ""
            raw_response: dict[str, Any] = {}
            error: str | None = None
            last_was_quota = False
            eval_result: dict[str, Any] = {"passed": False}

            system_prompt = (
                model_cfg.get("python_system_prompt", PYTHON_SYSTEM_PROMPT)
                if dataset_name == "python"
                else model_cfg.get("math_system_prompt", MATH_SYSTEM_PROMPT)
            )

            attempt = 0
            while attempt <= max_retries_transient:
                attempt += 1
                try:
                    last_error: Exception | None = None
                    for offset in range(len(tokens)):
                        token_index = (token_cursor + offset) % len(tokens)
                        token = tokens[token_index]
                        try:
                            logger.info(
                                "[%s][%s] (%d/%d) Sending %s (attempt=%d, key[%d]=%s)...",
                                dataset_name,
                                model_label,
                                done_now,
                                len(remaining),
                                key,
                                attempt,
                                token_index,
                                mask_token(token),
                            )
                            response_text, raw_response = call_chat_completion(
                                model_cfg=model_cfg,
                                prompt=row["prompt"],
                                system_prompt=system_prompt,
                                timeout_seconds=timeout_seconds,
                                token=token,
                            )
                            token_used = mask_token(token)
                            token_index_used = token_index
                            token_cursor = (token_index + 1) % len(tokens)
                            break
                        except Exception as exc:
                            last_error = exc
                            if is_quota_error(exc) and offset + 1 < len(tokens):
                                msg = f"token_index={token_index} ({mask_token(token)}): {exc}"
                                quota_errors.append(msg)
                                logger.warning(
                                    "[%s][%s] %s key[%d] hit quota; rotating to next key (%d/%d)",
                                    dataset_name,
                                    model_label,
                                    key,
                                    token_index,
                                    offset + 1,
                                    len(tokens),
                                )
                                continue
                            raise
                    else:
                        raise last_error or RuntimeError("No API token attempt completed")

                    if dataset_name == "python":
                        eval_result = evaluate_python_response(
                            response_text,
                            row,
                            timeout_seconds=eval_timeout_seconds,
                        )
                    else:
                        eval_result = evaluate_math_response(response_text, row)
                    error = None
                    last_was_quota = False
                    break
                except Exception as exc:  # noqa: BLE001
                    err_text = str(exc).lower()
                    last_was_quota = is_quota_error(exc)
                    is_transient = (
                        last_was_quota
                        or "http 503" in err_text
                        or "http 502" in err_text
                        or "http 500" in err_text
                        or "timed out" in err_text
                        or "temporarily unavailable" in err_text
                    )
                    if is_transient and attempt <= max_retries_transient:
                        backoff = quota_wait_seconds if last_was_quota else min(30, 5 * attempt)
                        logger.warning(
                            "[%s][%s] %s %s error on attempt %d/%d — sleeping %ds before retry. Detail: %s",
                            dataset_name,
                            model_label,
                            key,
                            "QUOTA" if last_was_quota else "TRANSIENT",
                            attempt,
                            max_retries_transient,
                            backoff,
                            str(exc)[:300],
                        )
                        time.sleep(backoff)
                        continue
                    if isinstance(exc, ResponseContentError):
                        raw_response = exc.parsed_response
                    eval_result = {"passed": False, "stderr": str(exc)}
                    error = str(exc)
                    break

            elapsed = round(time.time() - started, 3)
            usage = raw_response.get("usage", {}) if isinstance(raw_response, dict) else {}
            result = {
                "timestamp": datetime.now(UTC).isoformat(),
                "dataset": dataset_name,
                "model": model_cfg["model_name"],
                "model_label": model_label,
                "rep_id": rep_id,
                "row_key": key,
                "task_id": row["task_id"],
                "category_id": row["category_id"],
                "category_label": CATEGORY_LABELS.get(str(row["category_id"]), ""),
                "passed": bool(eval_result.get("passed")),
                "duration_seconds": elapsed,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "error": error,
                "is_quota_error": last_was_quota if error else False,
                "quota_errors": quota_errors,
                "token_index_used": token_index_used,
                "token_used": token_used,
                "eval_result": eval_result,
                "response_text": response_text,
                "raw_usage": usage,
            }

            if error is None:
                out.write(json.dumps(result, ensure_ascii=False) + "\n")
                out.flush()
                consecutive_quota_failures = 0
                if result["passed"]:
                    passed_now += 1
                logger.info(
                    "[%s][%s] (%d/%d) %s -> %s | %.2fs | tok=%s | key[%s]",
                    dataset_name,
                    model_label,
                    done_now,
                    len(remaining),
                    key,
                    "PASS" if result["passed"] else "FAIL",
                    elapsed,
                    result["completion_tokens"],
                    token_index_used,
                )
            else:
                errors_now += 1
                # Log full error into errors sidecar (do NOT pollute main JSONL with uncompleted quota errors)
                err_out.write(json.dumps(result, ensure_ascii=False) + "\n")
                err_out.flush()
                logger.error(
                    "[%s][%s] (%d/%d) %s -> ERROR (quota=%s) | %.2fs | %s",
                    dataset_name,
                    model_label,
                    done_now,
                    len(remaining),
                    key,
                    last_was_quota,
                    elapsed,
                    error[:400],
                )
                if last_was_quota:
                    consecutive_quota_failures += 1
                    if stop_after_quota_errors > 0 and consecutive_quota_failures >= stop_after_quota_errors:
                        stopped_for_quota = True
                        logger.error(
                            "[%s][%s] STOPPING EARLY after %d consecutive quota failures across all %d keys. "
                            "Progress is saved (%d/%d ok). Re-run the exact same command later to resume.",
                            dataset_name,
                            model_label,
                            consecutive_quota_failures,
                            len(tokens),
                            len(ok_keys) + (done_now - errors_now),
                            total_target,
                        )
                        break
                else:
                    consecutive_quota_failures = 0

            if delay > 0:
                time.sleep(delay)

    logger.info(
        "[%s][%s] Session summary: attempted=%d, passed=%d, errors=%d, stopped_for_quota=%s -> %s",
        dataset_name,
        model_label,
        done_now,
        passed_now,
        errors_now,
        stopped_for_quota,
        output_path,
    )
    return output_path, stopped_for_quota


def print_status(
    datasets: list[tuple[str, Path]],
    models: list[dict[str, Any]],
    wanted_cats: set[str],
    repeats: int,
    results_dir: Path,
) -> None:
    print(f"{'Dataset':<8} {'Model':<22} {'Target':>7} {'Done OK':>8} {'Remaining':>10} {'Err Log Lines':>14}")
    print("-" * 75)
    for dataset_name, csv_path in datasets:
        rows = [r for r in load_csv(csv_path) if str(r["category_id"]) in wanted_cats]
        target = len(rows) * repeats
        for model_cfg in models:
            model_label = str(model_cfg.get("name") or model_cfg["model_name"])
            out_dir = results_dir / dataset_name
            out_path = out_dir / f"{slugify(model_label)}.{dataset_name}.repeated.jsonl"
            err_path = out_dir / f"{slugify(model_label)}.{dataset_name}.errors.jsonl"
            ok_keys, _, _ = inspect_progress(out_path)
            err_lines = sum(1 for _ in err_path.open(encoding="utf-8")) if err_path.exists() else 0
            print(
                f"{dataset_name:<8} {model_label:<22} {target:>7} {len(ok_keys):>8} "
                f"{max(0, target - len(ok_keys)):>10} {err_lines:>14}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run k=3 independent repeated generations on the 6 core prompt conditions for API models."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_DIR)
    parser.add_argument("--log-file", type=Path, default=None, help="Explicit log file path.")
    parser.add_argument("--python-csv", type=Path, default=DEFAULT_PYTHON_CSV)
    parser.add_argument("--math-csv", type=Path, default=DEFAULT_MATH_CSV)
    parser.add_argument(
        "--dataset",
        choices=["python", "math", "both"],
        default="both",
        help="Which dataset to run (default: both).",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_STUDY_MODELS,
        help="Model names from .env.json (default: deepseek-v4-flash gemini-flash).",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=DEFAULT_CORE_CATEGORIES,
        help="Core category IDs to repeat (default: 1 2 3 4 7 13).",
    )
    parser.add_argument("--repeats", type=int, default=3, help="Independent repeats per cell (default: 3).")
    parser.add_argument("--limit-tasks", type=int, help="Optional cap on number of tasks (for smoke testing).")
    parser.add_argument("--timeout", type=int, default=120, help="API timeout seconds.")
    parser.add_argument("--eval-timeout", type=int, default=10, help="Python eval timeout seconds.")
    parser.add_argument("--max-retries", type=int, default=3, help="Transient/quota retry attempts per call.")
    parser.add_argument(
        "--quota-wait",
        type=int,
        default=60,
        help="Seconds to sleep when all keys hit quota before retrying a call (default: 60).",
    )
    parser.add_argument(
        "--stop-after-quota-errors",
        type=int,
        default=5,
        help="Stop early after N consecutive quota failures across all keys (default: 5; 0 disables).",
    )
    parser.add_argument("--delay", type=float, default=None, help="Override inter-call delay in seconds.")
    parser.add_argument("--clean-errors", action="store_true", help="Strip any prior error lines from main JSONL before running.")
    parser.add_argument("--status", action="store_true", help="Print progress table and exit without calling APIs.")
    parser.add_argument("--force", action="store_true", help="Ignore previously completed keys.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    all_models = config.get("models", [])
    wanted = set(args.models)
    models = [
        m for m in all_models if m.get("name") in wanted or m.get("model_name") in wanted
    ]
    if not models:
        raise SystemExit(f"No matching models found for {args.models} in {args.config}")

    wanted_cats = {str(c) for c in args.categories}
    datasets: list[tuple[str, Path]] = []
    if args.dataset in {"python", "both"}:
        datasets.append(("python", args.python_csv))
    if args.dataset in {"math", "both"}:
        datasets.append(("math", args.math_csv))

    if args.status:
        print_status(datasets, models, wanted_cats, args.repeats, args.results_dir)
        return

    logger, log_path = setup_logger(args.logs_dir, args.log_file)
    logger.info("Log file: %s", log_path)
    logger.info("Args: %s", vars(args))

    any_quota_stop = False
    for dataset_name, csv_path in datasets:
        all_rows = load_csv(csv_path)
        rows = [r for r in all_rows if str(r["category_id"]) in wanted_cats]
        if args.limit_tasks is not None:
            task_ids_ordered: list[str] = []
            seen: set[str] = set()
            for r in rows:
                tid = r["task_id"]
                if tid not in seen:
                    seen.add(tid)
                    task_ids_ordered.append(tid)
            keep_tasks = set(task_ids_ordered[: args.limit_tasks])
            rows = [r for r in rows if r["task_id"] in keep_tasks]

        for model_cfg in models:
            _, stopped_for_quota = run_repeated_dataset(
                dataset_name=dataset_name,
                rows=rows,
                model_cfg=model_cfg,
                results_dir=args.results_dir,
                repeats=args.repeats,
                timeout_seconds=args.timeout,
                eval_timeout_seconds=args.eval_timeout,
                max_retries_transient=args.max_retries,
                quota_wait_seconds=args.quota_wait,
                stop_after_quota_errors=args.stop_after_quota_errors,
                delay_override=args.delay,
                force=args.force,
                clean_errors=args.clean_errors,
                logger=logger,
            )
            if stopped_for_quota:
                any_quota_stop = True

    if any_quota_stop:
        logger.warning("Exiting with code %d due to quota exhaustion. Re-run the same command later to resume.", EXIT_QUOTA_EXHAUSTED)
        sys.exit(EXIT_QUOTA_EXHAUSTED)


if __name__ == "__main__":
    main()
