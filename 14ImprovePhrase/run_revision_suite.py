#!/usr/bin/env python3
"""Unified Cloud API runner for all remaining revision experiments (R1C4, R2C5/R2C14, R2C10, R2C7).

Reuses existing k=3 repeated-run data wherever possible so zero API calls are wasted:
  1. pipeline    (R1C4)       : Reuses Attempt 0 (rep_id=1) from results_api_repeated/python/
                                for 50 tasks x 3 policies (1, 3, 7 = 150 workflows).
                                Runs strict parser -> ast.parse -> tests, and makes REAL
                                follow-up retry calls (up to 2) ONLY on failed Attempt 0 rows.
  2. paraphrase  (R2C5/R2C14) : 30 Python tasks x 2 new neutral controls (short neutral
                                paraphrase + length-matched neutral prompt matching
                                polite/aggressive word count) = 60 calls.
                                Baseline (1), Polite (7), Aggressive (13) are reused.
  3. shared_task (R2C10)      : 20 Local TOANMATH Python tasks x 3 policies (1, 3, 7) = 60 calls
                                on Cloud API, directly comparable to already-collected Local runs.
  4. se_bench    (R2C7)       : 15 non-math SE Python tasks (se_benchmark_15.json) x 3 policies
                                (neutral_plaintext, neutral_xml, polite_plaintext) = 45 calls.

Total new calls for gemini-flash across all 4 suites: ~240-260 calls (~15 min).
Restart-safe, key-rotating, structured logs in 14ImprovePhrase/logs_revision/.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from subprocess import TimeoutExpired
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RUN_APIS_DIR = REPO_ROOT / "02ScalingPhrase" / "apimodel" / "run_apis"
LOCAL_PROBLEMS_CSV = REPO_ROOT / "02ScalingPhrase" / "localmodel" / "problems" / "problems.csv"
sys.path.insert(0, str(RUN_APIS_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from run_api_matrix import (  # noqa: E402
    PYTHON_SYSTEM_PROMPT,
    TEST_PREAMBLE,
    ResponseContentError,
    available_tokens,
    call_chat_completion,
    is_quota_error,
    load_csv,
    load_json,
    parse_json_list,
    slugify,
)
from run_api_repeated import EXIT_QUOTA_EXHAUSTED, setup_logger  # noqa: E402

DEFAULT_CONFIG_PATH = RUN_APIS_DIR / ".env.json"
DEFAULT_API_PYTHON_CSV = RUN_APIS_DIR / "problems.csv"
DEFAULT_API_REPEATED_DIR = SCRIPT_DIR / "results_api_repeated" / "python"
DEFAULT_SE_BENCH_JSON = SCRIPT_DIR / "se_benchmark_15.json"
DEFAULT_RESULTS_DIR = SCRIPT_DIR / "results_revision" / "api"
DEFAULT_LOGS_DIR = SCRIPT_DIR / "logs_revision"

POLICY_IDS = ["1", "3", "7"]
POLICY_LABELS = {
    "1": "neutral_plaintext",
    "3": "neutral_xml",
    "7": "polite_plaintext",
}

FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.S | re.I)

# Neutral paraphrase (same ~40-word length as baseline cat 1, different wording)
NEUTRAL_PARAPHRASE_PREFIX = (
    "You are an AI assistant focused on delivering accurate, clear responses.\n\n"
    "Below is a Python programming specification. Implement the requested function "
    "accurately using standard production conventions, complete type annotations, "
    "and appropriate error handling.\n\n"
    "Task: "
)

# Length-matched neutral prompt (~85 words, matching polite/aggressive framing length
# with purely neutral technical prose and zero social/emotional cues)
NEUTRAL_LENGTH_MATCHED_PREFIX = (
    "You are an AI assistant dedicated to providing clear and accurate information to support any request.\n\n"
    "The specification below defines a standalone Python programming task that will be verified "
    "automatically against unit tests. Read the problem description, function signature, input "
    "constraints, and example assertions carefully before writing your implementation. Complete "
    "the required function precisely as specified using only the Python standard library. Follow "
    "standard production software engineering practices, including clean modular structure, full "
    "type annotations for parameters and return values, and proper handling of boundary cases.\n\n"
    "Task: "
)

SE_TEMPLATES = {
    "neutral_plaintext": (
        "You are an AI assistant dedicated to providing clear and accurate information to support any request.\n\n"
        "Tasks are provided below. Complete the following Python requirement precisely as specified. "
        "Follow standard production practices, including full type hints and error handling.\n\n"
        "Task: {problem}"
    ),
    "neutral_xml": (
        "<prompt>\n<instruction>\n"
        "You are an AI assistant dedicated to providing clear and accurate information to support any request.\n\n"
        "Tasks are provided below. Complete the following Python requirement precisely as specified. "
        "Follow standard production practices, including full type hints and error handling.\n"
        "</instruction>\n<task>\n{problem}\n</task>\n</prompt>"
    ),
    "polite_plaintext": (
        "You are an AI assistant dedicated to providing clear and accurate information to support any request.\n\n"
        "Could you please help me solve this Python problem? I would really appreciate it if you could provide "
        "a high-quality solution. I would be so grateful if you could ensure the code is modular, includes full "
        "type hints, and handles errors correctly. Thank you so much for your help!\n\n"
        "Task: {problem}"
    ),
}


def strict_extract_code(text: str) -> str:
    if not text:
        return ""
    m = FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    s = text.strip()
    return s if s.startswith(("def ", "import ", "from ")) else ""


def run_downstream_consumer(
    response_text: str,
    tests: list[str],
    eval_timeout_seconds: int,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    if not response_text or not response_text.strip():
        return {
            "passed": False,
            "stage": "empty_response",
            "error_summary": "Empty model response.",
            "parse_ms": round((time.perf_counter() - t0) * 1000, 3),
            "validate_ms": 0.0,
            "exec_ms": 0.0,
        }
    code = strict_extract_code(response_text)
    parse_ms = round((time.perf_counter() - t0) * 1000, 3)
    if not code:
        return {
            "passed": False,
            "stage": "parse_fail",
            "error_summary": "Strict parser found no fenced Python block or bare Python definition.",
            "parse_ms": parse_ms,
            "validate_ms": 0.0,
            "exec_ms": 0.0,
        }

    tv = time.perf_counter()
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return {
            "passed": False,
            "stage": "syntax_fail",
            "error_summary": f"SyntaxError: {exc.msg} (line {exc.lineno})",
            "parse_ms": parse_ms,
            "validate_ms": round((time.perf_counter() - tv) * 1000, 3),
            "exec_ms": 0.0,
        }
    validate_ms = round((time.perf_counter() - tv) * 1000, 3)

    program = TEST_PREAMBLE + "\n" + code + "\n\n" + "\n".join(tests) + "\nprint('PASS')\n"
    te = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        sp = Path(tmpdir) / "candidate.py"
        sp.write_text(program, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(sp)],
                capture_output=True,
                text=True,
                timeout=eval_timeout_seconds,
            )
        except TimeoutExpired:
            return {
                "passed": False,
                "stage": "timeout",
                "error_summary": f"Timed out after {eval_timeout_seconds}s.",
                "parse_ms": parse_ms,
                "validate_ms": validate_ms,
                "exec_ms": round((time.perf_counter() - te) * 1000, 3),
            }
    exec_ms = round((time.perf_counter() - te) * 1000, 3)
    if proc.returncode == 0:
        return {
            "passed": True,
            "stage": "ok",
            "error_summary": "",
            "parse_ms": parse_ms,
            "validate_ms": validate_ms,
            "exec_ms": exec_ms,
        }
    lines = (proc.stderr or proc.stdout or "Failed").strip().splitlines()
    stage = "assertion_fail" if "AssertionError" in (proc.stderr or "") else "runtime_fail"
    return {
        "passed": False,
        "stage": stage,
        "error_summary": (lines[-1] if lines else stage)[:300],
        "parse_ms": parse_ms,
        "validate_ms": validate_ms,
        "exec_ms": exec_ms,
    }


def build_retry_prompt(orig_prompt: str, prev_stage: str, err_summary: str) -> str:
    if prev_stage in {"empty_response", "parse_fail", "syntax_fail"}:
        g = (
            f"Your previous output failed downstream validation ({prev_stage}: {err_summary}). "
            "Output ONLY valid, runnable Python code inside a single ```python ... ``` block "
            "with no surrounding prose or explanations."
        )
    else:
        g = (
            f"Your previous Python solution failed automated testing ({prev_stage}: {err_summary}). "
            "Fix the bug and output ONLY the corrected, runnable Python code inside a single "
            "```python ... ``` block with no explanations."
        )
    return f"{orig_prompt}\n\n[Pipeline Recovery Feedback]\n{g}"


def extract_task_payload(neutral_plaintext_prompt: str) -> str:
    marker = "Task:"
    idx = neutral_plaintext_prompt.find(marker)
    if idx >= 0:
        return neutral_plaintext_prompt[idx + len(marker) :].strip()
    return neutral_plaintext_prompt.strip()


def load_done_keys(path: Path, key_field: str = "item_key") -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("api_error") is None and rec.get(key_field):
                done.add(str(rec[key_field]))
    return done


def load_reusable_rep1(model_label: str) -> dict[tuple[str, str], dict[str, Any]]:
    """Load rep_id=1 records from existing k=3 API Python repeated runs."""
    path = DEFAULT_API_REPEATED_DIR / f"{slugify(model_label)}.python.repeated.jsonl"
    out: dict[tuple[str, str], dict[str, Any]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("error") is None and int(rec.get("rep_id", 0)) == 1:
                out[(str(rec["task_id"]), str(rec["category_id"]))] = rec
    return out


class ApiCaller:
    def __init__(
        self,
        model_cfg: dict[str, Any],
        timeout_seconds: int,
        max_http_retries: int,
        quota_wait_seconds: int,
        stop_after_quota_errors: int,
        delay_override: float | None,
        logger: logging.Logger,
    ) -> None:
        self.model_cfg = model_cfg
        self.model_label = str(model_cfg.get("name") or model_cfg["model_name"])
        self.tokens = available_tokens(model_cfg)
        if not self.tokens:
            raise ValueError(f"No token configured for {self.model_label}")
        self.cursor = 0
        self.timeout_seconds = timeout_seconds
        self.max_http_retries = max_http_retries
        self.quota_wait_seconds = quota_wait_seconds
        self.stop_after_quota_errors = stop_after_quota_errors
        self.delay = float(model_cfg.get("delay_seconds", 2)) if delay_override is None else delay_override
        self.logger = logger
        self.consecutive_quota = 0
        self.stopped_for_quota = False
        self.sys_prompt = model_cfg.get("python_system_prompt", PYTHON_SYSTEM_PROMPT)

    def call(self, prompt: str, tag: str) -> tuple[str, dict[str, Any], float, str | None]:
        t0 = time.perf_counter()
        attempt = 0
        while attempt <= self.max_http_retries:
            attempt += 1
            try:
                last_exc: Exception | None = None
                for offset in range(len(self.tokens)):
                    idx = (self.cursor + offset) % len(self.tokens)
                    tok = self.tokens[idx]
                    try:
                        txt, raw = call_chat_completion(
                            model_cfg=self.model_cfg,
                            prompt=prompt,
                            system_prompt=self.sys_prompt,
                            timeout_seconds=self.timeout_seconds,
                            token=tok,
                        )
                        self.cursor = (idx + 1) % len(self.tokens)
                        self.consecutive_quota = 0
                        llm_ms = round((time.perf_counter() - t0) * 1000, 3)
                        if self.delay > 0:
                            time.sleep(self.delay)
                        return txt, raw, llm_ms, None
                    except Exception as exc:
                        last_exc = exc
                        if is_quota_error(exc) and offset + 1 < len(self.tokens):
                            self.logger.warning("%s key[%d] quota hit; rotating", tag, idx)
                            continue
                        raise
                raise last_exc or RuntimeError("No API token succeeded")
            except Exception as exc:  # noqa: BLE001
                was_quota = is_quota_error(exc)
                err_l = str(exc).lower()
                is_transient = (
                    was_quota
                    or "http 503" in err_l
                    or "http 502" in err_l
                    or "http 500" in err_l
                    or "timed out" in err_l
                )
                if is_transient and attempt <= self.max_http_retries:
                    wait_s = self.quota_wait_seconds if was_quota else min(30, 5 * attempt)
                    self.logger.warning("%s transient error (%s), sleeping %ds", tag, str(exc)[:180], wait_s)
                    time.sleep(wait_s)
                    continue
                if was_quota:
                    self.consecutive_quota += 1
                    if self.stop_after_quota_errors > 0 and self.consecutive_quota >= self.stop_after_quota_errors:
                        self.stopped_for_quota = True
                raw_err = exc.parsed_response if isinstance(exc, ResponseContentError) else {}
                return "", raw_err, round((time.perf_counter() - t0) * 1000, 3), str(exc)
        return "", {}, round((time.perf_counter() - t0) * 1000, 3), "Exhausted HTTP retries"


def run_suite_pipeline(
    caller: ApiCaller,
    api_rows: list[dict[str, str]],
    out_dir: Path,
    max_retries: int,
    eval_timeout: int,
    logger: logging.Logger,
) -> None:
    """R1C4: Live 4-stage pipeline reusing Attempt 0 from k=3 runs; real retries only on failures."""
    out_path = out_dir / f"{slugify(caller.model_label)}.r1c4_pipeline.jsonl"
    done = load_done_keys(out_path)
    reusable = load_reusable_rep1(caller.model_label)
    rows = [r for r in api_rows if str(r["category_id"]) in POLICY_IDS]
    remaining = [r for r in rows if f"{r['task_id']}::{r['category_id']}" not in done]
    logger.info(
        "[R1C4 pipeline][%s] total=%d | done=%d | remaining=%d | reusable_rep1=%d",
        caller.model_label,
        len(rows),
        len(done),
        len(remaining),
        len(reusable),
    )

    with out_path.open("a", encoding="utf-8") as out:
        for idx, row in enumerate(remaining, start=1):
            if caller.stopped_for_quota:
                break
            tid, cid = str(row["task_id"]), str(row["category_id"])
            ikey = f"{tid}::{cid}"
            tests = parse_json_list(row.get("test_cases", "[]")) + parse_json_list(
                row.get("challenge_test_list", "[]")
            )
            attempts: list[dict[str, Any]] = []
            passed_at: int | None = None
            api_err: str | None = None

            # Attempt 0: reuse from k=3 rep_id=1 if available!
            prev = reusable.get((tid, cid))
            if prev is not None:
                resp0 = str(prev.get("response_text", ""))
                llm_ms0 = round(float(prev.get("duration_seconds", 0.0)) * 1000, 3)
                ptok0 = int(prev.get("prompt_tokens") or 0)
                ctok0 = int(prev.get("completion_tokens") or 0)
                reused_a0 = True
            else:
                tag0 = f"[R1C4][{caller.model_label}][{idx}/{len(remaining)}] {ikey} a0"
                resp0, raw0, llm_ms0, api_err = caller.call(row["prompt"], tag0)
                if api_err is not None:
                    logger.error("%s ERROR: %s", tag0, api_err[:200])
                    continue
                u0 = raw0.get("usage", {}) if isinstance(raw0, dict) else {}
                ptok0, ctok0 = int(u0.get("prompt_tokens", 0)), int(u0.get("completion_tokens", 0))
                reused_a0 = False

            c0 = run_downstream_consumer(resp0, tests, eval_timeout)
            attempts.append(
                {
                    "attempt": 0,
                    "reused_from_k3": reused_a0,
                    "passed": c0["passed"],
                    "stage": c0["stage"],
                    "error_summary": c0["error_summary"],
                    "llm_ms": llm_ms0,
                    "parse_ms": c0["parse_ms"],
                    "validate_ms": c0["validate_ms"],
                    "exec_ms": c0["exec_ms"],
                    "prompt_tokens": ptok0,
                    "completion_tokens": ctok0,
                    "response_text": resp0,
                }
            )
            if c0["passed"]:
                passed_at = 0
            else:
                prev_stage, prev_err = c0["stage"], c0["error_summary"]
                for r_idx in range(1, max_retries + 1):
                    retry_prompt = build_retry_prompt(row["prompt"], prev_stage, prev_err)
                    tag = f"[R1C4][{caller.model_label}][{idx}/{len(remaining)}] {ikey} retry={r_idx}"
                    logger.info("%s sending (prev=%s)...", tag, prev_stage)
                    resp_r, raw_r, llm_ms_r, api_err = caller.call(retry_prompt, tag)
                    if api_err is not None:
                        logger.error("%s ERROR: %s", tag, api_err[:200])
                        break
                    ur = raw_r.get("usage", {}) if isinstance(raw_r, dict) else {}
                    cr = run_downstream_consumer(resp_r, tests, eval_timeout)
                    attempts.append(
                        {
                            "attempt": r_idx,
                            "reused_from_k3": False,
                            "passed": cr["passed"],
                            "stage": cr["stage"],
                            "error_summary": cr["error_summary"],
                            "llm_ms": llm_ms_r,
                            "parse_ms": cr["parse_ms"],
                            "validate_ms": cr["validate_ms"],
                            "exec_ms": cr["exec_ms"],
                            "prompt_tokens": int(ur.get("prompt_tokens", 0)),
                            "completion_tokens": int(ur.get("completion_tokens", 0)),
                            "response_text": resp_r,
                        }
                    )
                    logger.info("%s -> %s (stage=%s, %.0fms)", tag, "PASS" if cr["passed"] else "FAIL", cr["stage"], llm_ms_r)
                    if cr["passed"]:
                        passed_at = r_idx
                        break
                    prev_stage, prev_err = cr["stage"], cr["error_summary"]

            if api_err is not None:
                continue

            rec = {
                "timestamp": datetime.now(UTC).isoformat(),
                "suite": "r1c4_pipeline",
                "regime": "api",
                "model": caller.model_cfg["model_name"],
                "model_label": caller.model_label,
                "item_key": ikey,
                "task_id": tid,
                "category_id": cid,
                "policy_label": POLICY_LABELS[cid],
                "attempts_used": len(attempts),
                "retries_used": len(attempts) - 1,
                "passed_r0": bool(attempts[0]["passed"]),
                "passed_r1": bool(passed_at is not None and passed_at <= 1),
                "passed_r2": bool(passed_at is not None and passed_at <= 2),
                "initial_stage": attempts[0]["stage"],
                "final_stage": attempts[-1]["stage"],
                "total_prompt_tokens": sum(a["prompt_tokens"] for a in attempts),
                "total_completion_tokens": sum(a["completion_tokens"] for a in attempts),
                "llm_total_ms": round(sum(a["llm_ms"] for a in attempts), 3),
                "consumer_total_ms": round(
                    sum(a["parse_ms"] + a["validate_ms"] + a["exec_ms"] for a in attempts), 3
                ),
                "api_error": None,
                "attempts": attempts,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()


def run_suite_paraphrase(
    caller: ApiCaller,
    api_rows: list[dict[str, str]],
    out_dir: Path,
    n_tasks: int,
    eval_timeout: int,
    logger: logging.Logger,
) -> None:
    """R2C5 + R2C14: 30 tasks x 2 new neutral controls (short paraphrase + length-matched neutral)."""
    out_path = out_dir / f"{slugify(caller.model_label)}.r2c5_r2c14_paraphrase.jsonl"
    done = load_done_keys(out_path)
    base_rows = [r for r in api_rows if str(r["category_id"]) == "1"][:n_tasks]

    variants = [
        ("neutral_paraphrase_short", NEUTRAL_PARAPHRASE_PREFIX),
        ("neutral_length_matched", NEUTRAL_LENGTH_MATCHED_PREFIX),
    ]
    schedule = [(vname, prefix, row) for vname, prefix in variants for row in base_rows]
    remaining = [x for x in schedule if f"{x[2]['task_id']}::{x[0]}" not in done]
    logger.info(
        "[R2C5/R2C14 paraphrase][%s] total=%d | done=%d | remaining=%d",
        caller.model_label,
        len(schedule),
        len(done),
        len(remaining),
    )

    with out_path.open("a", encoding="utf-8") as out:
        for idx, (vname, prefix, row) in enumerate(remaining, start=1):
            if caller.stopped_for_quota:
                break
            tid = str(row["task_id"])
            ikey = f"{tid}::{vname}"
            payload = extract_task_payload(row["prompt"])
            prompt = prefix + payload
            tests = parse_json_list(row.get("test_cases", "[]")) + parse_json_list(
                row.get("challenge_test_list", "[]")
            )
            tag = f"[R2C5/14][{caller.model_label}][{idx}/{len(remaining)}] {ikey}"
            logger.info("%s sending...", tag)
            resp, raw, llm_ms, api_err = caller.call(prompt, tag)
            if api_err is not None:
                logger.error("%s ERROR: %s", tag, api_err[:200])
                continue
            cons = run_downstream_consumer(resp, tests, eval_timeout)
            u = raw.get("usage", {}) if isinstance(raw, dict) else {}
            rec = {
                "timestamp": datetime.now(UTC).isoformat(),
                "suite": "r2c5_r2c14_paraphrase",
                "regime": "api",
                "model": caller.model_cfg["model_name"],
                "model_label": caller.model_label,
                "item_key": ikey,
                "task_id": tid,
                "variant": vname,
                "passed": cons["passed"],
                "stage": cons["stage"],
                "llm_ms": llm_ms,
                "prompt_tokens": int(u.get("prompt_tokens", 0)),
                "completion_tokens": int(u.get("completion_tokens", 0)),
                "api_error": None,
                "response_text": resp,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            logger.info("%s -> %s (%.0fms, tok=%s)", tag, "PASS" if cons["passed"] else "FAIL", llm_ms, rec["completion_tokens"])


def run_suite_shared_task(
    caller: ApiCaller,
    out_dir: Path,
    n_tasks: int,
    eval_timeout: int,
    logger: logging.Logger,
) -> None:
    """R2C10: Run 20 Local TOANMATH Python tasks x 3 policies on Cloud API (reuses Local runs)."""
    out_path = out_dir / f"{slugify(caller.model_label)}.r2c10_shared_task.jsonl"
    done = load_done_keys(out_path)
    local_rows = load_csv(LOCAL_PROBLEMS_CSV)
    # Pick first n_tasks distinct task_ids
    tids: list[str] = []
    for r in local_rows:
        if r["task_id"] not in tids:
            tids.append(r["task_id"])
            if len(tids) == n_tasks:
                break
    keep_tids = set(tids)
    rows = [r for r in local_rows if r["task_id"] in keep_tids and str(r["category_id"]) in POLICY_IDS]
    remaining = [r for r in rows if f"{r['task_id']}::{r['category_id']}" not in done]
    logger.info(
        "[R2C10 shared_task][%s] total=%d | done=%d | remaining=%d",
        caller.model_label,
        len(rows),
        len(done),
        len(remaining),
    )

    with out_path.open("a", encoding="utf-8") as out:
        for idx, row in enumerate(remaining, start=1):
            if caller.stopped_for_quota:
                break
            tid, cid = str(row["task_id"]), str(row["category_id"])
            ikey = f"{tid}::{cid}"
            tests = parse_json_list(row.get("test_cases", "[]")) + parse_json_list(
                row.get("challenge_test_list", "[]")
            )
            tag = f"[R2C10][{caller.model_label}][{idx}/{len(remaining)}] {ikey}"
            logger.info("%s sending...", tag)
            resp, raw, llm_ms, api_err = caller.call(row["prompt"], tag)
            if api_err is not None:
                logger.error("%s ERROR: %s", tag, api_err[:200])
                continue
            cons = run_downstream_consumer(resp, tests, eval_timeout)
            u = raw.get("usage", {}) if isinstance(raw, dict) else {}
            rec = {
                "timestamp": datetime.now(UTC).isoformat(),
                "suite": "r2c10_shared_task",
                "regime": "api_on_local_tasks",
                "model": caller.model_cfg["model_name"],
                "model_label": caller.model_label,
                "item_key": ikey,
                "task_id": tid,
                "category_id": cid,
                "policy_label": POLICY_LABELS[cid],
                "passed": cons["passed"],
                "stage": cons["stage"],
                "llm_ms": llm_ms,
                "prompt_tokens": int(u.get("prompt_tokens", 0)),
                "completion_tokens": int(u.get("completion_tokens", 0)),
                "api_error": None,
                "response_text": resp,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            logger.info("%s -> %s (%.0fms)", tag, "PASS" if cons["passed"] else "FAIL", llm_ms)


def run_suite_se_bench(
    caller: ApiCaller,
    out_dir: Path,
    eval_timeout: int,
    logger: logging.Logger,
) -> None:
    """R2C7: 15 independent non-math SE Python tasks x 3 policies = 45 calls."""
    out_path = out_dir / f"{slugify(caller.model_label)}.r2c7_se_bench.jsonl"
    done = load_done_keys(out_path)
    se_tasks = load_json(DEFAULT_SE_BENCH_JSON)
    schedule = [(t, pname, tmpl) for pname, tmpl in SE_TEMPLATES.items() for t in se_tasks]
    remaining = [x for x in schedule if f"{x[0]['task_id']}::{x[1]}" not in done]
    logger.info(
        "[R2C7 se_bench][%s] total=%d | done=%d | remaining=%d",
        caller.model_label,
        len(schedule),
        len(done),
        len(remaining),
    )

    with out_path.open("a", encoding="utf-8") as out:
        for idx, (task, pname, tmpl) in enumerate(remaining, start=1):
            if caller.stopped_for_quota:
                break
            tid = str(task["task_id"])
            ikey = f"{tid}::{pname}"
            prompt = tmpl.format(problem=task["prompt_body"])
            tag = f"[R2C7][{caller.model_label}][{idx}/{len(remaining)}] {ikey}"
            logger.info("%s sending...", tag)
            resp, raw, llm_ms, api_err = caller.call(prompt, tag)
            if api_err is not None:
                logger.error("%s ERROR: %s", tag, api_err[:200])
                continue
            cons = run_downstream_consumer(resp, task["tests"], eval_timeout)
            u = raw.get("usage", {}) if isinstance(raw, dict) else {}
            rec = {
                "timestamp": datetime.now(UTC).isoformat(),
                "suite": "r2c7_se_bench",
                "regime": "api",
                "model": caller.model_cfg["model_name"],
                "model_label": caller.model_label,
                "item_key": ikey,
                "task_id": tid,
                "domain": task["domain"],
                "policy_label": pname,
                "passed": cons["passed"],
                "stage": cons["stage"],
                "llm_ms": llm_ms,
                "prompt_tokens": int(u.get("prompt_tokens", 0)),
                "completion_tokens": int(u.get("completion_tokens", 0)),
                "api_error": None,
                "response_text": resp,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            logger.info("%s -> %s (%.0fms)", tag, "PASS" if cons["passed"] else "FAIL", llm_ms)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unified Cloud API runner for R1C4, R2C5/R2C14, R2C10, and R2C7."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_DIR)
    parser.add_argument("--models", nargs="+", default=["gemini-flash"])
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["all", "pipeline", "paraphrase", "shared_task", "se_bench"],
        default=["all"],
    )
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--paraphrase-tasks", type=int, default=30)
    parser.add_argument("--shared-tasks", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--eval-timeout", type=int, default=10)
    parser.add_argument("--http-retries", type=int, default=3)
    parser.add_argument("--quota-wait", type=int, default=60)
    parser.add_argument("--stop-after-quota-errors", type=int, default=5)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--status", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_json(args.config)
    wanted = set(args.models)
    models = [m for m in cfg.get("models", []) if m.get("name") in wanted or m.get("model_name") in wanted]
    if not models:
        raise SystemExit(f"No matching models for {args.models} in {args.config}")

    suites = (
        ["pipeline", "paraphrase", "shared_task", "se_bench"]
        if "all" in args.suites
        else args.suites
    )
    args.results_dir.mkdir(parents=True, exist_ok=True)

    if args.status:
        print(f"{'Model':<22} {'Suite':<22} {'Done':>6} {'Target':>7}")
        print("-" * 62)
        targets = {
            "r1c4_pipeline": 150,
            "r2c5_r2c14_paraphrase": args.paraphrase_tasks * 2,
            "r2c10_shared_task": args.shared_tasks * 3,
            "r2c7_se_bench": 45,
        }
        for m in models:
            lbl = str(m.get("name") or m["model_name"])
            for sname, tgt in targets.items():
                p = args.results_dir / f"{slugify(lbl)}.{sname}.jsonl"
                print(f"{lbl:<22} {sname:<22} {len(load_done_keys(p)):>6} {tgt:>7}")
        return

    logger, log_path = setup_logger(args.logs_dir)
    logger.info("Revision suite log: %s | suites=%s", log_path, suites)
    api_rows = load_csv(DEFAULT_API_PYTHON_CSV)

    any_quota = False
    for m in models:
        caller = ApiCaller(
            model_cfg=m,
            timeout_seconds=args.timeout,
            max_http_retries=args.http_retries,
            quota_wait_seconds=args.quota_wait,
            stop_after_quota_errors=args.stop_after_quota_errors,
            delay_override=args.delay,
            logger=logger,
        )
        if "pipeline" in suites and not caller.stopped_for_quota:
            run_suite_pipeline(caller, api_rows, args.results_dir, args.max_retries, args.eval_timeout, logger)
        if "paraphrase" in suites and not caller.stopped_for_quota:
            run_suite_paraphrase(caller, api_rows, args.results_dir, args.paraphrase_tasks, args.eval_timeout, logger)
        if "shared_task" in suites and not caller.stopped_for_quota:
            run_suite_shared_task(caller, args.results_dir, args.shared_tasks, args.eval_timeout, logger)
        if "se_bench" in suites and not caller.stopped_for_quota:
            run_suite_se_bench(caller, args.results_dir, args.eval_timeout, logger)
        if caller.stopped_for_quota:
            any_quota = True

    if any_quota:
        sys.exit(EXIT_QUOTA_EXHAUSTED)


if __name__ == "__main__":
    main()
