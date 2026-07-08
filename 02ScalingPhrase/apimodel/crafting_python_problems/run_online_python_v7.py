#!/usr/bin/env python3
"""Run v7 Python coding problems against OpenAI-compatible online models."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TASKS_PATH = SCRIPT_DIR / "base-mathproblems.bigmodel.v7.python.json"
DEFAULT_CONFIG_PATH = SCRIPT_DIR / ".env.json"
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results"


SYSTEM_PROMPT = """You are solving Python coding tasks.
Return only valid Python code.
Define exactly one function named solve_math_problem.
Do not include Markdown fences, explanation, print statements, or top-level test execution.
"""

TEST_PREAMBLE = """
from fractions import Fraction
import decimal
import itertools
import math
"""


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def endpoint_from_base(base_api: str) -> str:
    base_api = base_api.rstrip("/")
    if base_api.endswith("/chat/completions"):
        return base_api
    return f"{base_api}/chat/completions"


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-").lower()


def build_user_prompt(task: dict[str, Any]) -> str:
    tests = "\n".join(task.get("test_list", []))
    return (
        f"{task['text'].strip()}\n\n"
        "Your function must pass these examples:\n"
        f"{tests}\n\n"
        "Return only the Python source code."
    )


def call_chat_completion(
    model_cfg: dict[str, Any],
    task: dict[str, Any],
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    endpoint = endpoint_from_base(str(model_cfg["base_api"]))
    payload = {
        "model": model_cfg["model_name"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(task)},
        ],
        "temperature": model_cfg.get("temperature", 0),
        "max_tokens": model_cfg.get("max_tokens", 2048),
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {model_cfg['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc

    parsed = json.loads(raw)
    content = parsed["choices"][0]["message"]["content"]
    return content, parsed


def extract_python_code(response_text: str) -> str:
    fenced = re.search(r"```(?:python|py)?\s*(.*?)```", response_text, re.S | re.I)
    if fenced:
        return fenced.group(1).strip()
    return response_text.strip()


def validate_solution(code: str, task: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    assertions = task.get("test_list", []) + task.get("challenge_test_list", [])
    program = (
        TEST_PREAMBLE
        + "\n"
        + code
        + "\n\n"
        + "\n".join(assertions)
        + "\nprint('PASS')\n"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "candidate.py"
        script_path.write_text(program, encoding="utf-8")
        started = time.time()
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "duration_seconds": round(time.time() - started, 3),
    }


def load_completed_task_ids(path: Path) -> set[int]:
    completed: set[int] = set()
    if not path.exists():
        return completed
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            completed.add(int(row["task_id"]))
    return completed


def run_model(
    model_cfg: dict[str, Any],
    tasks: list[dict[str, Any]],
    results_dir: Path,
    timeout_seconds: int,
    eval_timeout_seconds: int,
    force: bool,
) -> None:
    model_label = model_cfg.get("name") or model_cfg["model_name"]
    output_path = results_dir / f"{slugify(str(model_label))}.v7.python.jsonl"
    completed = set() if force else load_completed_task_ids(output_path)
    delay = float(model_cfg.get("delay_seconds", 2))

    results_dir.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as out:
        for task in tasks:
            task_id = int(task["task_id"])
            if task_id in completed:
                continue
            print(f"[{model_label}] task {task_id}/{len(tasks)}", flush=True)
            started = time.time()
            try:
                response_text, raw_response = call_chat_completion(
                    model_cfg=model_cfg,
                    task=task,
                    timeout_seconds=timeout_seconds,
                )
                candidate_code = extract_python_code(response_text)
                eval_result = validate_solution(
                    candidate_code,
                    task,
                    timeout_seconds=eval_timeout_seconds,
                )
                error = None
            except Exception as exc:  # noqa: BLE001 - keep batch runs alive.
                response_text = ""
                raw_response = {}
                candidate_code = ""
                eval_result = {"passed": False, "stderr": str(exc)}
                error = str(exc)

            row = {
                "timestamp": datetime.utcnow().isoformat(),
                "model": model_cfg["model_name"],
                "model_label": model_label,
                "task_id": task_id,
                "old_id": task.get("old_id"),
                "passed": bool(eval_result.get("passed")),
                "duration_seconds": round(time.time() - started, 3),
                "eval_result": eval_result,
                "error": error,
                "response_text": response_text,
                "candidate_code": candidate_code,
                "raw_usage": raw_response.get("usage", {}),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            if delay > 0:
                time.sleep(delay)

    print(f"[{model_label}] wrote {output_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run base-mathproblems v7 Python tasks with online models."
    )
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--model", help="Run only config entry whose name/model_name matches.")
    parser.add_argument("--start", type=int, default=1, help="First 1-based task_id to run.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of tasks.")
    parser.add_argument("--timeout", type=int, default=120, help="API timeout in seconds.")
    parser.add_argument("--eval-timeout", type=int, default=10, help="Local test timeout in seconds.")
    parser.add_argument("--force", action="store_true", help="Do not skip existing task ids.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks = load_json(args.tasks)
    tasks = [task for task in tasks if int(task["task_id"]) >= args.start]
    if args.limit is not None:
        tasks = tasks[: args.limit]

    config = load_json(args.config)
    models = config.get("models", [])
    if args.model:
        models = [
            model
            for model in models
            if args.model in {model.get("name"), model.get("model_name")}
        ]
    if not models:
        raise SystemExit("No models selected. Check .env.json or --model.")

    for model_cfg in models:
        run_model(
            model_cfg=model_cfg,
            tasks=tasks,
            results_dir=args.results_dir,
            timeout_seconds=args.timeout,
            eval_timeout_seconds=args.eval_timeout,
            force=args.force,
        )


if __name__ == "__main__":
    main()
