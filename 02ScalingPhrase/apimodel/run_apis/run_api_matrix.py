#!/usr/bin/env python3
"""Run prompt-matrix CSVs against OpenAI-compatible API models.

The script is intentionally dependency-free so the run_apis folder can be copied
to a remote server and executed with only Python installed.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import operator
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / ".env.json"
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results"
DEFAULT_PYTHON_CSV = SCRIPT_DIR / "problems.csv"
DEFAULT_MATH_CSV = SCRIPT_DIR / "problems.math.csv"


PYTHON_SYSTEM_PROMPT = "Output only the code, no explanations."
MATH_SYSTEM_PROMPT = "Output only the final result, no explanations."

TEST_PREAMBLE = """
from fractions import Fraction
import decimal
import itertools
import math
"""


class ResponseContentError(RuntimeError):
    """Raised when an API response does not contain message.content."""

    def __init__(self, parsed_response: dict[str, Any]) -> None:
        self.parsed_response = parsed_response
        formatted = json.dumps(parsed_response, ensure_ascii=False, sort_keys=True)
        super().__init__(f"Missing message.content in API response: {formatted}")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def endpoint_from_base(base_api: str) -> str:
    base_api = base_api.rstrip("/")
    if base_api.endswith("/chat/completions"):
        return base_api
    return f"{base_api}/chat/completions"


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-").lower()


def row_key(row: dict[str, str]) -> str:
    return f"{row['task_id']}::{row['category_id']}"


def available_tokens(model_cfg: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    primary = str(model_cfg.get("token", "")).strip()
    if primary:
        tokens.append(primary)
    for token in model_cfg.get("tokens", []) or []:
        token = str(token).strip()
        if token and token not in tokens:
            tokens.append(token)
    return tokens


def mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def is_quota_error(error: Exception | str) -> bool:
    text = str(error).lower()
    return (
        "http 429" in text
        or "resource_exhausted" in text
        or "quota" in text
        or "rate-limit" in text
        or "rate limit" in text
    )


def call_chat_completion(
    model_cfg: dict[str, Any],
    prompt: str,
    system_prompt: str,
    timeout_seconds: int,
    token: str,
) -> tuple[str, dict[str, Any]]:
    payload = {
        "model": model_cfg["model_name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": model_cfg.get("temperature", 0),
        "max_tokens": model_cfg.get("max_tokens", 2048),
    }
    request = urllib.request.Request(
        endpoint_from_base(str(model_cfg["base_api"])),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": str(model_cfg.get("user_agent", "curl/8.7.1")),
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
    try:
        content = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ResponseContentError(parsed) from exc
    return content, parsed


def extract_python_code(response_text: str) -> str:
    fenced = re.search(r"```(?:python|py)?\s*(.*?)```", response_text, re.S | re.I)
    if fenced:
        return fenced.group(1).strip()
    return response_text.strip()


def parse_json_list(value: str) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON list, got {type(parsed).__name__}")
    return [str(item) for item in parsed]


def evaluate_python_response(
    response_text: str,
    row: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    code = extract_python_code(response_text)
    tests = parse_json_list(row.get("test_cases", "[]"))
    challenge_tests = parse_json_list(row.get("challenge_test_list", "[]"))
    program = (
        TEST_PREAMBLE
        + "\n"
        + code
        + "\n\n"
        + "\n".join(tests + challenge_tests)
        + "\nprint('PASS')\n"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "candidate.py"
        script_path.write_text(program, encoding="utf-8")
        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except TimeoutExpired as exc:
            return {
                "passed": False,
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or str(exc),
                "candidate_code": code,
                "duration_seconds": round(time.time() - started, 3),
                "timeout": True,
            }

    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "candidate_code": code,
        "duration_seconds": round(time.time() - started, 3),
    }


def normalize_response_text(response: str) -> str:
    """Keep only the likely final answer from a model response."""
    text = str(response).strip()
    text = re.sub(r"```(?:text|json|python)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "").strip()
    text = text.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")

    boxed = extract_latex_command_argument(text, "boxed")
    if boxed is not None:
        text = boxed.strip()

    marker_patterns = [
        r"(?:final answer|answer|result)\s*(?:is|:)?\s*(.+)$",
        r"(?:therefore|so),?\s*(.+)$",
    ]
    for pattern in marker_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if matches:
            text = matches[-1].strip()
            break

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and line.strip() not in {"\\[", "\\]", "$$", "$"}
    ]
    if lines:
        text = lines[-1]
    return text.strip().strip(".")


def extract_latex_command_argument(text: str, command: str) -> str | None:
    marker = f"\\{command}" + "{"
    start = text.rfind(marker)
    if start < 0:
        return None
    index = start + len(marker)
    depth = 1
    chars = []
    while index < len(text):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(chars)
        chars.append(char)
        index += 1
    return None


def _replace_latex_frac(text: str) -> str:
    pattern = re.compile(r"\\(?:dfrac|tfrac|frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
    previous = None
    while previous != text:
        previous = text
        text = pattern.sub(r"(\1)/(\2)", text)
    return text


def normalize_math_expression(value: Any) -> str:
    text = str(value).strip()
    text = text.strip("$ ")
    text = text.replace("\\(", "").replace("\\)", "")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("{,}", ",")
    text = text.replace(",", "")
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("×", "*").replace("·", "*").replace("\\cdot", "*")
    text = text.replace("^", "**")
    text = _replace_latex_frac(text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", text)
    text = re.sub(r"√\s*([0-9.]+)", r"sqrt(\1)", text)
    return text.strip()


_ALLOWED_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_ALLOWED_NAMES = {"pi": math.pi, "e": math.e}
_ALLOWED_FUNCS = {"sqrt": math.sqrt}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY:
        return _ALLOWED_BINARY[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in _ALLOWED_NAMES:
        return float(_ALLOWED_NAMES[node.id])
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _ALLOWED_FUNCS
        and len(node.args) == 1
    ):
        return float(_ALLOWED_FUNCS[node.func.id](_safe_eval(node.args[0])))
    raise ValueError(f"Unsupported math expression: {ast.dump(node)}")


def parse_math_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize_math_expression(value)
    if not text:
        raise ValueError("empty math value")
    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()
    if re.fullmatch(r"[-+]?\d+", text):
        result = float(int(text, 10))
        return result / 100 if is_percent else result
    parsed = ast.parse(text, mode="eval")
    result = float(_safe_eval(parsed))
    return result / 100 if is_percent else result


def extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text, including fractions and simple LaTeX formulas."""
    text = normalize_response_text(text)

    candidates = [text]
    if "=" in text:
        candidates.append(text.split("=")[-1].strip())
    for candidate in candidates:
        try:
            return [parse_math_value(candidate)]
        except Exception:
            pass

    values: list[float] = []
    token_pattern = re.compile(
        r"\\(?:dfrac|tfrac|frac)\s*\{[^{}]+\}\s*\{[^{}]+\}"
        r"|\\sqrt\s*\{[^{}]+\}"
        r"|sqrt\s*\([^()]+\)"
        r"|√\s*[0-9.]+"
        r"|[-+]?\d[\d,]*(?:\.\d+)?\s*/\s*[-+]?\d[\d,]*(?:\.\d+)?"
        r"|[-+]?\d[\d,]*(?:\.\d+)?\s*%?"
        r"|[-+]?\.\d+\s*%?"
    )
    for match in token_pattern.finditer(text):
        try:
            values.append(parse_math_value(match.group(0)))
        except Exception:
            continue
    return values


def parse_expected_answer(raw_value: str) -> float | list[float]:
    try:
        loaded = json.loads(raw_value)
    except Exception:
        loaded = raw_value
    if isinstance(loaded, list):
        return [parse_math_value(item) for item in loaded]
    return parse_math_value(loaded)


def evaluate_math_response(response_text: str, row: dict[str, str], tolerance: float = 1e-6) -> dict[str, Any]:
    expected_answer = parse_expected_answer(row.get("expected_answer", ""))
    expected_values = expected_answer if isinstance(expected_answer, list) else [expected_answer]
    numbers = extract_numbers(response_text)

    errors = []
    if len(numbers) < len(expected_values):
        errors.append(
            f"Expected {len(expected_values)} numeric value(s), extracted {len(numbers)}: {numbers}"
        )
        return {
            "passed": False,
            "values_passed": 0,
            "values_total": len(expected_values),
            "expected_answer": expected_answer,
            "extracted_values": numbers,
            "errors": errors,
        }

    candidate_values = numbers[-len(expected_values) :]
    passed_count = 0
    for actual, expected in zip(candidate_values, expected_values):
        if abs(actual - expected) <= tolerance:
            passed_count += 1
        else:
            errors.append(f"Expected {expected}, got {actual}")

    return {
        "passed": passed_count == len(expected_values),
        "values_passed": passed_count,
        "values_total": len(expected_values),
        "expected_answer": expected_answer,
        "extracted_values": candidate_values,
        "errors": errors,
    }


def load_completed_keys(path: Path) -> set[str]:
    completed: set[str] = set()
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
            completed.add(str(row.get("row_key")))
    return completed


def select_rows(
    rows: list[dict[str, str]],
    start: int,
    limit: int | None,
    task_id: str | None,
    category_id: str | None,
) -> list[dict[str, str]]:
    indexed = list(enumerate(rows, start=1))
    indexed = [(i, row) for i, row in indexed if i >= start]
    if task_id is not None:
        indexed = [(i, row) for i, row in indexed if row["task_id"] == task_id]
    if category_id is not None:
        indexed = [(i, row) for i, row in indexed if row["category_id"] == category_id]
    if limit is not None:
        indexed = indexed[:limit]
    return [row | {"_row_number": str(i)} for i, row in indexed]


def run_dataset(
    dataset_name: str,
    rows: list[dict[str, str]],
    model_cfg: dict[str, Any],
    results_dir: Path,
    timeout_seconds: int,
    eval_timeout_seconds: int,
    force: bool,
) -> None:
    model_label = str(model_cfg.get("name") or model_cfg["model_name"])
    output_dir = results_dir / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{slugify(model_label)}.{dataset_name}.jsonl"
    completed = set() if force else load_completed_keys(output_path)
    delay = float(model_cfg.get("delay_seconds", 2))
    tokens = available_tokens(model_cfg)
    if not tokens:
        raise ValueError(f"No token configured for model {model_label}")

    with output_path.open("a", encoding="utf-8") as out:
        for row in rows:
            key = row_key(row)
            if key in completed:
                continue
            print(
                f"[{dataset_name}][{model_label}] row {row['_row_number']} "
                f"task={row['task_id']} category={row['category_id']}",
                flush=True,
            )
            started = time.time()
            token_used = ""
            token_index_used: int | None = None
            quota_errors: list[str] = []
            response_text = ""
            raw_response: dict[str, Any] = {}
            try:
                last_error: Exception | None = None
                for token_index, token in enumerate(tokens):
                    try:
                        response_text, raw_response = call_chat_completion(
                            model_cfg=model_cfg,
                            prompt=row["prompt"],
                            system_prompt=(
                                model_cfg.get("python_system_prompt", PYTHON_SYSTEM_PROMPT)
                                if dataset_name == "python"
                                else model_cfg.get("math_system_prompt", MATH_SYSTEM_PROMPT)
                            ),
                            timeout_seconds=timeout_seconds,
                            token=token,
                        )
                        token_used = mask_token(token)
                        token_index_used = token_index
                        break
                    except Exception as exc:
                        last_error = exc
                        if is_quota_error(exc) and token_index + 1 < len(tokens):
                            quota_errors.append(f"token_index={token_index}: {exc}")
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
            except Exception as exc:  # noqa: BLE001 - preserve batch progress.
                if isinstance(exc, ResponseContentError):
                    raw_response = exc.parsed_response
                eval_result = {"passed": False, "stderr": str(exc)}
                error = str(exc)

            result = {
                "timestamp": datetime.now(UTC).isoformat(),
                "dataset": dataset_name,
                "model": model_cfg["model_name"],
                "model_label": model_label,
                "row_number": int(row["_row_number"]),
                "row_key": key,
                "task_id": row["task_id"],
                "category_id": row["category_id"],
                "passed": bool(eval_result.get("passed")),
                "duration_seconds": round(time.time() - started, 3),
                "error": error,
                "quota_errors": quota_errors,
                "token_index_used": token_index_used,
                "token_used": token_used,
                "eval_result": eval_result,
                "response_text": response_text,
                "raw_response": raw_response,
                "raw_usage": raw_response.get("usage", {}),
            }
            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()
            if delay > 0:
                time.sleep(delay)

    print(f"[{dataset_name}][{model_label}] wrote {output_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run problems.csv and/or problems.math.csv with configured API models."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--python-csv", type=Path, default=DEFAULT_PYTHON_CSV)
    parser.add_argument("--math-csv", type=Path, default=DEFAULT_MATH_CSV)
    parser.add_argument(
        "--dataset",
        choices=["python", "math", "both"],
        default="both",
        help="Which CSV to run.",
    )
    parser.add_argument("--model", help="Run one model by config name or model_name.")
    parser.add_argument("--start", type=int, default=1, help="First 1-based CSV row.")
    parser.add_argument("--limit", type=int, help="Maximum rows per dataset.")
    parser.add_argument("--task-id", help="Only run rows for this task_id.")
    parser.add_argument("--category-id", help="Only run rows for this category_id/template.")
    parser.add_argument("--timeout", type=int, default=120, help="API timeout seconds.")
    parser.add_argument("--eval-timeout", type=int, default=10, help="Python eval timeout seconds.")
    parser.add_argument("--force", action="store_true", help="Do not skip completed row keys.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
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

    datasets: list[tuple[str, Path]] = []
    if args.dataset in {"python", "both"}:
        datasets.append(("python", args.python_csv))
    if args.dataset in {"math", "both"}:
        datasets.append(("math", args.math_csv))

    for dataset_name, csv_path in datasets:
        rows = select_rows(
            load_csv(csv_path),
            start=args.start,
            limit=args.limit,
            task_id=args.task_id,
            category_id=args.category_id,
        )
        for model_cfg in models:
            run_dataset(
                dataset_name=dataset_name,
                rows=rows,
                model_cfg=model_cfg,
                results_dir=args.results_dir,
                timeout_seconds=args.timeout,
                eval_timeout_seconds=args.eval_timeout,
                force=args.force,
            )


if __name__ == "__main__":
    main()
