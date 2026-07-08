"""Run VietJack single-answer math tasks on Ollama cloud models.

Outputs one JSONL result file per model plus a summary JSON file. The script is
restart-safe: existing task_id rows in an output file are skipped.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any


DEFAULT_MODELS = [
    "ministral-3:8b-cloud",
    "nemotron-3-nano:30b-cloud",
    "rnj-1:8b-cloud",
    "gemma3:4b-cloud",
    "gemma3:12b-cloud",
]

DEFAULT_TASKS_PATH = Path("problems/VietJack_OnVao10_2026.math.v5.json")
DEFAULT_OUTPUT_DIR = Path("results_vietjack_math_cloud")
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
SYSTEM_PROMPT = "Return only the final numeric result. Do not include explanation or units."


def safe_model_name(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", model).strip("-")


def load_tasks(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        tasks = json.load(handle)
    if limit is not None:
        return tasks[:limit]
    return tasks


def completed_task_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_id = record.get("task_id")
            if task_id:
                completed.add(str(task_id))
    return completed


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def call_ollama(
    model: str,
    prompt: str,
    ollama_url: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> tuple[str, dict[str, Any]]:
    start = time.time()
    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    try:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{ollama_url.rstrip('/')}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("response", ""), {
            "success": True,
            "error": "",
            "duration_seconds": time.time() - start,
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_duration_ns": data.get("total_duration", 0),
            "load_duration_ns": data.get("load_duration", 0),
            "prompt_eval_duration_ns": data.get("prompt_eval_duration", 0),
            "eval_duration_ns": data.get("eval_duration", 0),
            "done_reason": data.get("done_reason", ""),
        }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", "replace")
        return "", {
            "success": False,
            "error": f"HTTP {exc.code}: {error_body}",
            "duration_seconds": time.time() - start,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration_ns": 0,
            "load_duration_ns": 0,
            "prompt_eval_duration_ns": 0,
            "eval_duration_ns": 0,
            "done_reason": "",
        }
    except Exception as exc:  # noqa: BLE001 - preserve failures as records.
        return "", {
            "success": False,
            "error": str(exc),
            "duration_seconds": time.time() - start,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_duration_ns": 0,
            "load_duration_ns": 0,
            "prompt_eval_duration_ns": 0,
            "eval_duration_ns": 0,
            "done_reason": "",
        }


def normalize_response_text(response: str) -> str:
    text = response.strip()
    text = re.sub(r"```(?:text|json|python)?\s*", "", text, flags=re.I)
    text = text.replace("```", "").strip()
    marker_patterns = [
        r"(?:final answer|answer|result)\s*(?:is|:)?\s*(.+)$",
        r"(?:therefore|so),?\s*(.+)$",
    ]
    for pattern in marker_patterns:
        matches = re.findall(pattern, text, flags=re.I | re.S)
        if matches:
            text = matches[-1].strip()
            break
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        text = lines[-1]
    return text.strip().rstrip(".")


def parse_number_token(token: str) -> float | None:
    token = token.strip()
    token = token.replace(",", "")
    if not token:
        return None
    sqrt_value = parse_sqrt_token(token)
    if sqrt_value is not None:
        return sqrt_value
    is_percent = token.endswith("%")
    token = token.rstrip("%").strip()
    try:
        if "/" in token:
            value = float(Fraction(re.sub(r"\s+", "", token)))
        else:
            value = float(token)
    except Exception:
        return None
    return value / 100 if is_percent else value


def parse_sqrt_token(token: str) -> float | None:
    normalized = re.sub(r"\s+", "", token.strip())
    normalized = normalized.replace("\\sqrt", "sqrt").replace("√", "sqrt")
    match = re.fullmatch(r"(?:(-?\d+(?:\.\d+)?)\*)?sqrt(?:\{([^{}]+)\}|\(([^()]+)\)|(-?\d+(?:\.\d+)?))", normalized)
    if not match:
        return None
    coefficient_text, braced, parenthesized, plain = match.groups()
    radicand_text = braced or parenthesized or plain
    try:
        coefficient = float(coefficient_text) if coefficient_text else 1.0
        radicand = float(Fraction(radicand_text))
    except Exception:
        return None
    if radicand < 0:
        return None
    return coefficient * math.sqrt(radicand)


def extract_numeric_values(response: str) -> list[float]:
    text = normalize_response_text(response)
    sqrt_values: list[float] = []
    sqrt_pattern = re.compile(r"(?:-?\d+(?:\.\d+)?\s*\*?\s*)?(?:\\sqrt\s*\{[^{}]+\}|sqrt\s*(?:\([^()]+\)|\{[^{}]+\}|-?\d+(?:\.\d+)?)|√\s*-?\d+(?:\.\d+)?)")
    for match in sqrt_pattern.finditer(text):
        value = parse_sqrt_token(match.group(0))
        if value is not None:
            sqrt_values.append(value)
    if sqrt_values:
        return sqrt_values
    values: list[float] = []
    pattern = re.compile(r"[-+]?(?:\d+\s*/\s*\d+|\d+(?:\.\d+)?|\.\d+)\s*%?")
    for match in pattern.finditer(text):
        value = parse_number_token(match.group(0))
        if value is not None:
            values.append(value)
    return values


def expected_to_float(expected: Any) -> float:
    if isinstance(expected, (int, float)):
        return float(expected)
    parsed = parse_number_token(str(expected))
    if parsed is None:
        raise ValueError(f"Expected answer is not numeric: {expected!r}")
    return parsed


def almost_equal(actual: float, expected: float, tolerance: float) -> bool:
    if math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        return True
    return False


def evaluate_answer(
    response_text: str,
    expected_answer: Any,
    tolerance: float,
) -> dict[str, Any]:
    expected_value = expected_to_float(expected_answer)
    values = extract_numeric_values(response_text)
    if not values:
        return {
            "passed": False,
            "values_passed": 0,
            "values_total": 1,
            "expected_value": expected_value,
            "extracted_values": values,
            "errors": ["No numeric value extracted"],
        }
    candidate = values[-1]
    passed = almost_equal(candidate, expected_value, tolerance)
    return {
        "passed": passed,
        "values_passed": 1 if passed else 0,
        "values_total": 1,
        "expected_value": expected_value,
        "extracted_values": values,
        "candidate_value": candidate,
        "errors": [] if passed else [f"Expected {expected_value}, got {candidate}"],
    }


def build_prompt(task: dict[str, Any]) -> str:
    return (
        "Solve the following math problem. Return only the final numeric result.\n\n"
        f"{task['prompt']}"
    )


def summarize_file(path: Path) -> dict[str, Any]:
    total = passed = failed_calls = 0
    durations: list[float] = []
    completion_tokens: list[int] = []
    if not path.exists():
        return {
            "result_file": str(path),
            "rows": 0,
            "passed": 0,
            "pass_rate": 0,
            "failed_calls": 0,
            "avg_duration_seconds": 0,
            "avg_completion_tokens": 0,
        }
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            passed += int(bool(record.get("passed")))
            failed_calls += int(not bool(record.get("call_success", True)))
            durations.append(float(record.get("duration_seconds") or 0))
            completion_tokens.append(int(record.get("completion_tokens") or 0))
    return {
        "result_file": str(path),
        "rows": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0,
        "failed_calls": failed_calls,
        "avg_duration_seconds": sum(durations) / total if total else 0,
        "avg_completion_tokens": sum(completion_tokens) / total if total else 0,
    }


def run_model(
    model: str,
    tasks: list[dict[str, Any]],
    tasks_path: Path,
    output_dir: Path,
    ollama_url: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
    tolerance: float,
    delay: float,
) -> dict[str, Any]:
    dataset_name = tasks_path.name.replace(".json", "")
    output_path = output_dir / f"{safe_model_name(model)}.{dataset_name}.jsonl"
    completed = completed_task_ids(output_path)
    remaining = [task for task in tasks if task["id"] not in completed]
    print(
        f"\nModel {model}: {len(completed)} completed, "
        f"{len(remaining)} remaining, output={output_path}",
        flush=True,
    )

    for index, task in enumerate(remaining, start=1):
        print(f"[{model}] {index}/{len(remaining)} {task['id']}...", end=" ", flush=True)
        response_text, meta = call_ollama(
            model=model,
            prompt=build_prompt(task),
            ollama_url=ollama_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        if meta["success"]:
            eval_result = evaluate_answer(response_text, task["expected_answer"], tolerance)
            status = "PASS" if eval_result["passed"] else "FAIL"
            print(f"{status} {eval_result.get('values_passed', 0)}/1", flush=True)
        else:
            eval_result = {
                "passed": False,
                "values_passed": 0,
                "values_total": 1,
                "expected_value": expected_to_float(task["expected_answer"]),
                "extracted_values": [],
                "errors": [meta["error"]],
            }
            print(f"ERROR {meta['error']}", flush=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "task_id": task["id"],
            "category": task.get("category", ""),
            "difficulty": task.get("difficulty", ""),
            "source_task_id": task.get("source_task_id", ""),
            "source_old_id": task.get("source_old_id", ""),
            "prompt": task["prompt"],
            "expected_answer": task["expected_answer"],
            "passed": eval_result["passed"],
            "values_passed": eval_result["values_passed"],
            "values_total": eval_result["values_total"],
            "expected_value": eval_result["expected_value"],
            "extracted_values": eval_result["extracted_values"],
            "candidate_value": eval_result.get("candidate_value"),
            "errors": eval_result["errors"],
            "call_success": meta["success"],
            "call_error": meta["error"],
            "duration_seconds": meta["duration_seconds"],
            "prompt_tokens": meta["prompt_tokens"],
            "completion_tokens": meta["completion_tokens"],
            "total_duration_ns": meta["total_duration_ns"],
            "load_duration_ns": meta["load_duration_ns"],
            "prompt_eval_duration_ns": meta["prompt_eval_duration_ns"],
            "eval_duration_ns": meta["eval_duration_ns"],
            "done_reason": meta["done_reason"],
            "response_text": response_text,
        }
        append_jsonl(output_path, record)
        if delay > 0:
            time.sleep(delay)

    return {"model": model, **summarize_file(output_path)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run VietJack single-answer math tasks on Ollama cloud models."
    )
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--delay", type=float, default=0.2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(args.tasks, args.limit)
    print(f"Loaded {len(tasks)} tasks from {args.tasks}")
    print(f"Models: {', '.join(args.models)}")
    summaries = []
    for model in args.models:
        summaries.append(
            run_model(
                model=model,
                tasks=tasks,
                tasks_path=args.tasks,
                output_dir=args.output_dir,
                ollama_url=args.ollama_url,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                tolerance=args.tolerance,
                delay=args.delay,
            )
        )
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "tasks": str(args.tasks),
                "task_count": len(tasks),
                "ollama_url": args.ollama_url,
                "models": args.models,
                "summaries": summaries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSummary written to {summary_path}")


if __name__ == "__main__":
    main()
