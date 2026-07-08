#!/usr/bin/env python3
"""
generate_dataset.py — Automated MBPP-style dataset generator for Vietnamese math problems.

Reads problems from a markdown file, calls an LLM to generate canonical Python solutions
with test cases, self-verifies + auto-corrects assertion values, and appends to a JSON dataset.
"""

import os
import re
import json
import time
import math
import argparse
import urllib.request
import urllib.error
import traceback
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
env_vars = {}
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
except FileNotFoundError:
    pass

API_BASE = env_vars.get("API_BASE", os.environ.get("API_BASE", "http://localhost:11434/v1")).rstrip("/")
API_KEY = env_vars.get("API_KEY", os.environ.get("API_KEY", "dummy"))
MODEL = env_vars.get("MODEL", os.environ.get("MODEL", "gemma3:12b-cloud"))

# MD_PATH is now configurable via CLI arguments
JSON_PATH = "problems/VNSchoolMathProblems.v0.2.json"
FAILED_DIR = "logs/generation_failures"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert mathematician and Python developer creating evaluation datasets for coding LLMs (similar to MBPP).
Your goal is to parse a Vietnamese math problem, translate it to English, write canonical high-precision Python code to solve it, and provide test cases.

Respond ONLY with a JSON object (no markdown fences, no extra text):
{
  "task_id": <int>,
  "text": "<Concise English translation. Keep all math entities and rounding rules. If data is missing (tables/images), describe what the parameters represent.>",
  "code": "<Python code>",
  "test_list": [
    "assert <function_name>(...) == <val>",
    "assert <function_name>(...) == <val>"
  ],
  "test_setup_code": "",
  "challenge_test_list": [
    "assert ...", "assert ...", "assert ...", "assert ...", "assert ..."
  ]
}

CRITICAL RULES:
1. The function MUST accept parameters. NO parameterless functions. If key data is missing (tables/images), use parameters for those values.
2. test_list must have exactly 2 tests. challenge_test_list must have exactly 5 tests. All 7 tests MUST use DIFFERENT parameter values.
3. Use ONLY standard Python libraries (math, itertools, functools, etc.). NO scipy, numpy, pandas.
4. test_setup_code MUST be an empty string "".
5. Keep the code concise (under 30 lines of logic). No "thinking out loud" comments (no "Wait...", "Actually...", "Let me re-verify...").
6. Do not include dead code, unused variables, or unreachable imports.
7. Ensure all rounding rules in the problem are respected.
"""

# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------
def extract_problems(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [p.strip() for p in re.findall(r"^\+ (.*?)$", text, re.MULTILINE)]


# ---------------------------------------------------------------------------
# LLM caller
# ---------------------------------------------------------------------------
def call_llm(problem_text, task_id):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = (
        f"Problem {task_id}:\n{problem_text}\n\n"
        f"Return the JSON structure for this problem with task_id={task_id}."
    )
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/chat/completions", data=data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            content = res_json["choices"][0]["message"]["content"]

        # Robust JSON extraction: look for all blocks starting with { and ending with }
        json_blocks = re.findall(r'\{.*\}', content, re.DOTALL)
        if not json_blocks:
             # Fallback: maybe it's just raw JSON without fences or the regex failed on newlines
             try:
                 return json.loads(content.strip())
             except:
                 pass
        
        for block in json_blocks:
            try:
                # Try to find the outermost {} if there are nested ones or multiple objects
                # A simple way is to find the first { and the last } in the string
                first_brace = content.find('{')
                last_brace = content.rfind('}')
                if first_brace != -1 and last_brace != -1:
                    candidate = content[first_brace:last_brace+1]
                    # But wait, the LLM might have output two separate objects. 
                    # Let's try to parse the whole block first, then try the first one.
                    try:
                        return json.loads(candidate)
                    except:
                        # If that fails, maybe there are multiple top-level objects?
                        # Let's try to find the first complete object
                        obj_count = 0
                        for i, char in enumerate(candidate):
                            if char == '{': obj_count += 1
                            elif char == '}': obj_count -= 1
                            if obj_count == 0:
                                try:
                                    return json.loads(candidate[:i+1])
                                except:
                                    break
                return json.loads(block)
            except json.JSONDecodeError:
                continue

        print(f"  JSON parse error: Could not find valid JSON in content")
        _dump_failure(task_id, content if "content" in dir() else "N/A", "No valid JSON found")
        return None
    except Exception as e:
        print(f"  LLM call error: {e}")
        return None


# ---------------------------------------------------------------------------
# Self-verification & auto-correction
# ---------------------------------------------------------------------------
def verify_entry(entry):
    """Execute canonical code against all its assertions. Returns (pass_count, total, errors)."""
    code = entry.get("code", "")
    tests = entry.get("test_list", []) + entry.get("challenge_test_list", [])
    exec_globals = {}
    try:
        exec(code, exec_globals)
    except Exception as e:
        return 0, len(tests), [f"CODE_EXEC_ERROR: {e}"]

    passed = 0
    errors = []
    for test in tests:
        try:
            exec(test, exec_globals)
            passed += 1
        except AssertionError:
            errors.append(f"ASSERT_FAIL: {test[:100]}")
        except Exception as e:
            errors.append(f"RUNTIME_ERROR in '{test[:60]}': {e}")

    return passed, len(tests), errors


def _parse_assert(test_str):
    """Parse 'assert func(args) == expected' into (call_str, expected_str, comparator).
    Returns (call_str, expected_str, comparator) or None on failure.
    comparator is '==' or custom like 'abs(...) < ...'
    """
    test_str = test_str.strip()
    if not test_str.startswith("assert "):
        return None

    expr = test_str[7:].strip()

    # Handle: assert abs(func(...) - val) < eps
    abs_match = re.match(r"abs\((.+?)\s*-\s*(.+?)\)\s*<\s*(.+)", expr)
    if abs_match:
        return abs_match.group(1).strip(), abs_match.group(2).strip(), "abs"

    # Handle: assert func(...) == val
    if " == " in expr:
        parts = expr.rsplit(" == ", 1)
        return parts[0].strip(), parts[1].strip(), "=="

    return None


def auto_fix_assertions(entry):
    """Run the canonical code and recompute expected values for all assertions.
    Returns the fixed entry (mutated in place)."""
    code = entry.get("code", "")
    exec_globals = {}
    try:
        exec(code, exec_globals)
    except Exception:
        return entry  # Can't fix if code itself is broken

    def fix_test_list(tests):
        fixed = []
        for test in tests:
            parsed = _parse_assert(test)
            if parsed is None:
                fixed.append(test)
                continue

            call_str, expected_str, comparator = parsed

            try:
                actual = eval(call_str, exec_globals)
            except Exception:
                fixed.append(test)  # Can't evaluate — keep original
                continue

            if comparator == "==":
                fixed.append(f"assert {call_str} == {repr(actual)}")
            elif comparator == "abs":
                fixed.append(f"assert abs({call_str} - {repr(actual)}) < 1e-9")
            else:
                fixed.append(test)

        return fixed

    entry["test_list"] = fix_test_list(entry.get("test_list", []))
    entry["challenge_test_list"] = fix_test_list(entry.get("challenge_test_list", []))
    return entry


# ---------------------------------------------------------------------------
# Structural validation
# ---------------------------------------------------------------------------
def validate_structure(entry):
    """Check that the entry has the right shape. Returns list of issues."""
    issues = []
    required = ["task_id", "text", "code", "test_list", "challenge_test_list"]
    for key in required:
        if key not in entry:
            issues.append(f"Missing key: {key}")

    if "code" in entry:
        # Must define at least one function
        if "def " not in entry["code"]:
            issues.append("Code does not define any function")
        # Must not import forbidden libs
        for lib in ["scipy", "numpy", "pandas", "sklearn"]:
            if lib in entry["code"]:
                issues.append(f"Forbidden library: {lib}")

    if "test_list" in entry and len(entry["test_list"]) < 1:
        issues.append("test_list is empty")
    if "challenge_test_list" in entry and len(entry["challenge_test_list"]) < 1:
        issues.append("challenge_test_list is empty")

    return issues


# ---------------------------------------------------------------------------
# Failure logging
# ---------------------------------------------------------------------------
def _dump_failure(task_id, raw_content, error_msg):
    os.makedirs(FAILED_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(FAILED_DIR, f"task_{task_id}_{ts}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Error: {error_msg}\n\n---RAW OUTPUT---\n{raw_content}\n")
    print(f"  Failure logged to {path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run(args):
    problems = extract_problems(args.input_md)
    print(f"Total problems in markdown: {len(problems)}")

    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    else:
        dataset = []

    last_id = max((t["task_id"] for t in dataset), default=0)
    next_idx = args.start_idx  # 0-indexed into problems list

    generated = 0
    skipped = 0
    stats = {"pass": 0, "auto_fixed": 0, "failed": 0, "skipped": 0}

    while generated < args.batch_size and next_idx < len(problems):
        current_task_id = last_id + 1
        vietnamese_text = problems[next_idx]

        print(f"\n{'='*60}")
        print(f"[{generated+1}/{args.batch_size}] Task {current_task_id} (model: {MODEL})")
        print(f"  Input: {vietnamese_text[:100]}...")

        success = False

        for attempt in range(1, args.max_retries + 1):
            print(f"  Attempt {attempt}/{args.max_retries}...", end=" ")
            start = time.time()

            entry = call_llm(vietnamese_text, current_task_id)
            elapsed = time.time() - start

            if entry is None:
                print(f"LLM returned None ({elapsed:.1f}s)")
                time.sleep(2)
                continue

            # Structural validation
            issues = validate_structure(entry)
            if issues:
                print(f"Structural issues: {issues} ({elapsed:.1f}s)")
                time.sleep(2)
                continue

            # Force task_id and clean test_setup_code
            entry["task_id"] = current_task_id
            entry["test_setup_code"] = ""

            # Step 1: Verify raw output
            passed, total, errors = verify_entry(entry)

            if passed == total and total > 0:
                print(f"PASS ({passed}/{total}) ({elapsed:.1f}s)")
                stats["pass"] += 1
                success = True
                break

            # Step 2: Auto-fix assertions
            print(f"raw={passed}/{total}, auto-fixing...", end=" ")
            entry = auto_fix_assertions(entry)

            # Step 3: Re-verify after fix
            passed2, total2, errors2 = verify_entry(entry)
            if passed2 == total2 and total2 > 0:
                print(f"FIXED ({passed2}/{total2}) ({elapsed:.1f}s)")
                stats["auto_fixed"] += 1
                success = True
                break
            else:
                print(f"still failing ({passed2}/{total2}) ({elapsed:.1f}s)")
                if errors2:
                    for e in errors2[:3]:
                        print(f"    {e}")
                stats["failed"] += 1
                time.sleep(2)

        if success:
            entry["original_vn"] = vietnamese_text
            entry["success"] = True
            dataset.append(entry)
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved Task {current_task_id}")
            last_id += 1
            generated += 1
        else:
            print(f"  ✗ Skipping Task {current_task_id} after {args.max_retries} attempts")
            stats["skipped"] += 1
            skipped += 1

        next_idx += 1
        time.sleep(4)

    # Summary
    print(f"\n{'='*60}")
    print(f"GENERATION COMPLETE")
    print(f"  Generated: {generated}")
    print(f"  Skipped:   {skipped}")
    print(f"  Stats:     {stats}")
    print(f"  Dataset:   {len(dataset)} total tasks in {JSON_PATH}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate MBPP-style math dataset")
    p.add_argument("--batch-size", type=int, default=1, help="Number of problems to generate")
    p.add_argument("--max-retries", type=int, default=3, help="Max LLM retries per problem")
    p.add_argument("--input-md", type=str, default="problems/VNSchoolMathProblems2026/exam_problems.md", help="Path to markdown problems file")
    p.add_argument("--start-idx", type=int, default=0, help="Starting index in the markdown file")
    run(p.parse_args())
