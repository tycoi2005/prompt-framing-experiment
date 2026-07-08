#!/usr/bin/env python3
"""Evaluate LLM code generation against MBPP tasks.

Workflow:
  1. Load tasks from mbpp.jsonl or sanitized-mbpp.json (or any MBPP-format JSON file).
  2. For each task, build a prompt from the task description and test signatures.
  3. Send the prompt to an LLM via an OpenAI-compatible chat API.
  4. Extract Python code from the LLM response.
  5. Execute the extracted code together with the task's test assertions.
  6. Log results (pass/fail, tokens, latency, errors) to a JSONL checkpoint file.

Supports resume after interruption — already-completed trials are skipped.

Configuration:
  API settings are read from CLI flags, environment variables, or a .env file
  (same scheme as generate_prompt_matrix.py).

Usage:
  # Dry run (no LLM call, fills response with placeholder):
  python3 evaluate_mbpp.py --dry-run

  # Evaluate 3 specific tasks against the full MBPP dataset:
  python3 evaluate_mbpp.py --dataset full --task-ids 1 2 3

  # Evaluate all sanitized tasks with a custom model:
  python3 evaluate_mbpp.py --dataset sanitized --model gpt-4.1-mini

  # Use an Ollama-compatible local model:
  python3 evaluate_mbpp.py --api-base http://localhost:11434/v1 --model qwen2.5:7b

  # Resume after a crash:
  python3 evaluate_mbpp.py --resume
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error, request


# ---------------------------------------------------------------------------
# Task Loading
# ---------------------------------------------------------------------------

def load_tasks(path: Path) -> List[Dict[str, Any]]:
    """Load MBPP tasks from a JSONL or JSON file (auto-detected)."""
    with open(path, "r", encoding="utf-8") as f:
        head = f.read(2).strip()

    if head.startswith("["):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        tasks: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks


# ---------------------------------------------------------------------------
# Prompt Building  (mirrors the notebook's build_user_prompt)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an expert Python programmer. "
    "Write a Python function that solves the given task. "
    "Your code should pass the provided test cases. "
    "Provide your final answer as code inside a ```python code block."
)


def build_user_prompt(task: Dict[str, Any]) -> str:
    """Build the user prompt sent to the LLM for a given MBPP task."""
    # 'text' is used in full MBPP; 'prompt' is used in sanitized
    description = task.get("text") or task.get("prompt", "")

    # Gather test info so the model knows the expected interface
    test_list = task.get("test_list", [])
    test_imports = task.get("test_imports", [])
    setup_code = task.get("test_setup_code", "")

    parts = [f"Task: {description}"]

    if test_imports:
        parts.append(f"\nRequired imports:\n{chr(10).join(test_imports)}")

    if setup_code:
        parts.append(f"\nSetup code:\n{setup_code}")

    if test_list:
        parts.append(f"\nYour code should pass these tests:\n{chr(10).join(test_list)}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# LLM Calling  (OpenAI-compatible chat completions API)
# ---------------------------------------------------------------------------

def load_dotenv(dotenv_path: Path) -> Dict[str, str]:
    """Minimal .env loader (same as generate_prompt_matrix.py)."""
    values: Dict[str, str] = {}
    if not dotenv_path.exists():
        return values
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def get_setting(name: str, dotenv_values: Dict[str, str], default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return dotenv_values.get(name, default)


def resolve_api_url(base: str, endpoint: str) -> str:
    if endpoint.startswith("http"):
        return endpoint
    base = base.rstrip("/")
    endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    if base.endswith(endpoint):
        return base
    return f"{base}{endpoint}"


def call_chat_completion(
    *,
    api_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> Tuple[str, Dict[str, Any]]:
    """Call an OpenAI-compatible chat completions endpoint.

    Returns (response_text, metadata_dict).
    """
    start = time.time()

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        return "", {
            "duration": time.time() - start,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "success": False,
            "error": f"HTTP {exc.code}: {details}",
        }
    except error.URLError as exc:
        return "", {
            "duration": time.time() - start,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "success": False,
            "error": f"Network error: {exc.reason}",
        }

    data = json.loads(raw)
    choices = data.get("choices", [])
    content = ""
    if choices:
        content = choices[0].get("message", {}).get("content", "")

    usage = data.get("usage", {})
    return content, {
        "duration": time.time() - start,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "success": True,
        "error": "",
    }


# ---------------------------------------------------------------------------
# Code Extraction  (mirrors the notebook's extract_python_code)
# ---------------------------------------------------------------------------

def extract_python_code(response: str) -> str:
    """Extract Python code from an LLM response containing markdown code blocks."""
    # Try ```python blocks first
    matches = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
    if matches:
        return matches[-1].strip()

    # Try generic ``` blocks
    matches = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
    if matches:
        return matches[-1].strip()

    # Fallback: find lines starting with def/class
    lines = response.split("\n")
    code_lines: List[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith(("def ", "class ", "import ", "from ")):
            in_code = True
        if in_code:
            code_lines.append(line)
    return "\n".join(code_lines).strip()


# ---------------------------------------------------------------------------
# Code Evaluation (sandboxed via multiprocessing)
# ---------------------------------------------------------------------------

def _exec_worker(
    code: str,
    setup_code: str,
    test_imports: List[str],
    test_list: List[str],
    challenge_test_list: List[str],
    result_queue: multiprocessing.Queue,
) -> None:
    """Execute code and each test individually in an isolated process."""
    imports_block = "\n".join(test_imports) if test_imports else ""
    # Combine imports, setup, and code to initialize the workspace
    init_code = f"{imports_block}\n{setup_code}\n{code}\n"
    
    global_ns: Dict[str, Any] = {}
    all_tests = test_list + challenge_test_list
    total_count = len(all_tests)
    
    try:
        exec(init_code, global_ns)  # noqa: S102
    except Exception:
        # Code itself failed to initialize (SyntaxError, etc.)
        result_queue.put({
            "passed_count": 0,
            "total_count": total_count,
            "errors": [traceback.format_exc()]
        })
        return

    # Run each test assertion individually
    passed_count = 0
    errors: List[str] = []
    
    for test in all_tests:
        try:
            # We use the same global_ns so state persists between tests 
            # (though assertions usually shouldn't depend on each other)
            exec(test, global_ns)  # noqa: S102
            passed_count += 1
        except Exception:
            errors.append(f"Test failed: {test}\n{traceback.format_exc()}")
            
    result_queue.put({
        "passed_count": passed_count,
        "total_count": total_count,
        "errors": errors
    })


def evaluate_code(
    extracted_code: str,
    task: Dict[str, Any],
    exec_timeout: int = 10,
) -> Dict[str, Any]:
    """Run the extracted code against standard and challenge tests."""
    setup_code = task.get("test_setup_code", "")
    test_imports = task.get("test_imports", [])
    test_list = task.get("test_list", [])
    challenge_test_list = task.get("challenge_test_list", [])
    
    if not extracted_code:
        return {
            "passed_count": 0,
            "total_count": len(test_list) + len(challenge_test_list),
            "errors": ["No code extracted from response"]
        }

    result_queue: multiprocessing.Queue = multiprocessing.Queue()  # type: ignore[type-arg]
    proc = multiprocessing.Process(
        target=_exec_worker,
        args=(extracted_code, setup_code, test_imports, test_list, challenge_test_list, result_queue),
    )
    proc.start()
    proc.join(exec_timeout)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {
            "passed_count": 0,
            "total_count": len(test_list) + len(challenge_test_list),
            "errors": [f"Execution timed out after {exec_timeout}s"]
        }

    if result_queue.empty():
        return {
            "passed_count": 0,
            "total_count": len(test_list) + len(challenge_test_list),
            "errors": ["Worker crashed without reporting result"]
        }

    return result_queue.get()


# ---------------------------------------------------------------------------
# Checkpoint (auto-save / resume)
# ---------------------------------------------------------------------------

def save_checkpoint(results: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_checkpoint(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    results: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def completed_keys(results: List[Dict[str, Any]]) -> set:
    return {
        (r["task_id"], r.get("run_id", 1))
        for r in results
        if r.get("response_length", 0) > 0 or r.get("tests_passed", 0) > 0
    }


# ---------------------------------------------------------------------------
# Main Experiment Runner
# ---------------------------------------------------------------------------

def run_experiment(
    tasks: List[Dict[str, Any]],
    args: argparse.Namespace,
    api_url: str,
    api_key: str,
    model: str,
    debug_log_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    checkpoint_path = Path(args.checkpoint)
    runs = args.runs

    # Resume logic
    if args.resume:
        results = load_checkpoint(checkpoint_path)
        done = completed_keys(results)
        print(f"Resuming: found {len(done)} completed trials in checkpoint")
    else:
        results = []
        done: set = set()

    total = len(tasks) * runs
    print(f"Total trials: {total} ({total - len(done)} remaining)")
    print(f"Model: {model}")
    print(f"Runs per task: {runs}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)

    count = 0
    consecutive_errors = 0

    for task in tasks:
        task_id = task.get("task_id")
        for run_id in range(1, runs + 1):
            count += 1
            key = (task_id, run_id)
            if key in done:
                continue

            user_prompt = build_user_prompt(task)
            sys_prompt = args.system_prompt or SYSTEM_PROMPT
            print(f"[{count}/{total}] task={task_id} run={run_id}...", end=" ", flush=True)

            if debug_log_path:
                with open(debug_log_path, "a", encoding="utf-8") as df:
                    log_entry = (
                        f"\n{'='*80}\n"
                        f"TASK: {task_id} | RUN: {run_id}\n"
                        f"{'='*80}\n"
                        f"SYSTEM PROMPT:\n{sys_prompt}\n"
                        f"{'-'*40}\n"
                        f"USER PROMPT:\n{user_prompt}\n"
                        f"{'='*80}\n"
                    )
                    df.write(log_entry)
                # print(f"\n[DEBUG] PROMPT:\n{user_prompt}\n{'-'*20}") # Removed console flood by default

            # Call LLM (or dry-run)
            if args.dry_run:
                canonical = task.get("code", "# no code")
                response_text = f"```python\n{canonical}\n```"
                meta = {
                    "duration": 0.0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "success": True,
                    "error": "",
                }
            else:
                for attempt in range(3):
                    response_text, meta = call_chat_completion(
                        api_url=api_url,
                        api_key=api_key,
                        model=model,
                        system_prompt=sys_prompt,
                        user_prompt=user_prompt,
                        temperature=args.temperature,
                        max_tokens=args.max_tokens,
                        timeout=args.timeout,
                    )
                    if meta["success"]:
                        consecutive_errors = 0
                        break
                    else:
                        consecutive_errors += 1
                        if attempt < 2:
                            print("RETRY...", end=" ", flush=True)
                            time.sleep(3)

            if debug_log_path:
                with open(debug_log_path, "a", encoding="utf-8") as df:
                    df.write(f"LLM RESPONSE:\n{response_text}\n{'='*80}\n")
                if args.debug:
                    # Print brief excerpt if debug is on
                    short_resp = response_text[:200] + "..." if len(response_text) > 200 else response_text
                    print(f"\n[DEBUG] RESPONSE EXCERPT: {short_resp}")

            if not meta["success"]:
                print(f"ERROR: {meta['error']}")
                results.append({
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "task_id": task_id,
                    "run_id": run_id,
                    "passed": False,
                    "tests_passed": 0,
                    "tests_total": len(task.get("test_list", [])) + len(task.get("challenge_test_list", [])),
                    "error": meta["error"],
                    "duration_seconds": meta["duration"],
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "response_length": 0,
                    "response_text": "",
                    "extracted_code": "",
                })
            else:
                extracted = extract_python_code(response_text)
                eval_result = evaluate_code(extracted, task, exec_timeout=args.exec_timeout)

                passed_n = eval_result["passed_count"]
                total_n = eval_result["total_count"]
                
                status = "PASS" if passed_n == total_n else "FAIL"
                print(f"{status} ({passed_n}/{total_n} passed) ({meta['duration']:.1f}s)")

                if passed_n < total_n and args.verbose:
                    first_err = eval_result["errors"][0] if eval_result["errors"] else "Unknown error"
                    print(f"  First Error: {first_err.splitlines()[-1]}")

                results.append({
                    "timestamp": datetime.now().isoformat(),
                    "model": model,
                    "task_id": task_id,
                    "run_id": run_id,
                    "passed": passed_n == total_n,
                    "tests_passed": passed_n,
                    "tests_total": total_n,
                    "errors": eval_result["errors"],
                    "duration_seconds": meta["duration"],
                    "prompt_tokens": meta["prompt_tokens"],
                    "completion_tokens": meta["completion_tokens"],
                    "total_tokens": meta["prompt_tokens"] + meta["completion_tokens"],
                    "response_length": len(response_text),
                    "response_text": response_text,
                    "extracted_code": extracted,
                })

            save_checkpoint(results, checkpoint_path)

            if args.sleep > 0:
                time.sleep(args.sleep)

    save_checkpoint(results, checkpoint_path)
    print(f"\n{'=' * 60}")
    print(f"EXPERIMENT COMPLETE: {len(results)} trials")

    all_passed = sum(1 for r in results if r.get("tests_passed") == r.get("tests_total"))
    print(f"Fully Passed: {all_passed}  |  Pass rate: {all_passed / max(len(results), 1) * 100:.1f}%")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate LLM code generation against MBPP tasks.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Data
    parser.add_argument("--dataset", default="full", choices=["full", "sanitized"],
                        help="Dataset version (default: full)")
    parser.add_argument("--data-file", default="",
                        help="Path to a custom MBPP-format JSON/JSONL file")
    parser.add_argument("--task-ids", nargs="+", type=int, default=[],
                        help="Evaluate only these task IDs")
    parser.add_argument("--base-dir", default=".",
                        help="Directory for datasets (if not relative)")

    # API
    parser.add_argument("--dotenv", default=".env", help="Path to .env file")
    parser.add_argument("--api-base", default="", help="Override API_BASE")
    parser.add_argument("--api-key", default="", help="Override API_KEY")
    parser.add_argument("--model", default="", help="Override MODEL")
    parser.add_argument("--api-endpoint", default="", help="Override API_ENDPOINT")

    # Generation params
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout")

    # Execution
    parser.add_argument("--exec-timeout", type=int, default=10, help="Code execution timeout")
    parser.add_argument("--runs", type=int, default=1, help="Runs per task")
    parser.add_argument("--sleep", type=float, default=0.0, help="Delay between calls")

    # Output organization
    parser.add_argument("--checkpoint", default="", help="Custom checkpoint path")
    parser.add_argument("--logs-dir", default="logs", help="Folder for debug logs")
    parser.add_argument("--checkpoints-dir", default="checkpoints", help="Folder for JSONL results")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--verbose", action="store_true", help="Show error snippets")
    parser.add_argument("--debug", action="store_true", help="Log prompts and responses")

    # Prompt
    parser.add_argument("--system-prompt", default="",
                        help="Override the default system prompt")

    # Dry run
    parser.add_argument("--dry-run", action="store_true", help="Use canonical code")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir)

    # Folders
    Path(args.checkpoints_dir).mkdir(parents=True, exist_ok=True)
    Path(args.logs_dir).mkdir(parents=True, exist_ok=True)

    # Resolve data file
    if args.data_file:
        data_path = Path(args.data_file)
    else:
        file_map = {
            "full": base_dir / "mbpp.jsonl",
            "sanitized": base_dir / "sanitized-mbpp.json",
        }
        data_path = file_map[args.dataset]

    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        sys.exit(1)

    tasks = load_tasks(data_path)
    print(f"Loaded {len(tasks)} tasks from {data_path}")

    if args.task_ids:
        tasks = [t for t in tasks if t.get("task_id") in args.task_ids]

    # API resolve
    dotenv_path = Path(args.dotenv)
    if not dotenv_path.is_absolute():
        dotenv_path = base_dir / dotenv_path
    dotenv_values = load_dotenv(dotenv_path)

    api_base = args.api_base or get_setting("API_BASE", dotenv_values)
    api_key = args.api_key or get_setting("API_KEY", dotenv_values)
    model = args.model or get_setting("MODEL", dotenv_values, "gpt-4.1-mini")
    endpoint = args.api_endpoint or get_setting("API_ENDPOINT", dotenv_values, "/chat/completions")
    api_url = resolve_api_url(api_base, endpoint) if not args.dry_run else ""

    model_tag = model.replace(":", "-").replace("/", "-")
    
    # Paths
    if not args.checkpoint:
        args.checkpoint = str(Path(args.checkpoints_dir) / f"checkpoint_{model_tag}.jsonl")

    debug_log_path = None
    if args.debug:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_log_path = Path(args.logs_dir) / f"debug_{model_tag}_{ts}.log"
        print(f"Debug logging enabled: {debug_log_path}")

    print(f"Checkpoint location: {args.checkpoint}")

    run_experiment(tasks, args, api_url, api_key, model, debug_log_path)


if __name__ == "__main__":
    main()
