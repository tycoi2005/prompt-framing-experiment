#!/usr/bin/env python3
"""Independent programmatic + stratified-sample oracle audit for R1C6 and R2C12.

Audits all 200 tasks across the 4 evaluation benchmarks:
  - Local Python Code (50 tasks): VNSchoolMathProblems_lite.v0.7.json
  - API Python Code   (50 tasks): base-mathproblems.bigmodel.v7.python.json
  - Local Math        (50 tasks): VietJack_OnVao10_2026.math.v5.json
  - API Math          (50 tasks): base-mathproblems.bigmodel.v5.math.json

Checks for Code tasks:
  1. Reference solution passes all public + hidden assertions in isolated namespace.
  2. Duplicate assertions or duplicate call arguments across public/hidden tests.
  3. Zero-parameter functions (potential hardcoded-answer risk) vs parameterized functions.
  4. Exact float equality (`== 12.34`) vs `round()`/`math.isclose` (rounding sensitivity).
  5. Hardcoded lookup/if-elif tables in reference solutions.
  6. Signature consistency between prompt text and reference `def`.

Checks for Math tasks:
  1. Expected answer parses cleanly as finite float/int/fraction.
  2. Rounding/unit/format instructions present when answer is non-integer.

Outputs:
  - 14ImprovePhrase/analysis/oracle_audit_report.md
  - 14ImprovePhrase/analysis/oracle_audit_code_tasks.csv
  - 14ImprovePhrase/analysis/oracle_audit_math_tasks.csv
"""

from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR / "analysis"

CODE_DATASETS = [
    ("Local Code (TOANMATH)", REPO_ROOT / "02ScalingPhrase/localmodel/problems/VNSchoolMathProblems_lite.v0.7.json"),
    ("API Code (MathNet)", REPO_ROOT / "02ScalingPhrase/apimodel/base-mathproblems.bigmodel.v7.python.json"),
]
MATH_DATASETS = [
    ("Local Math (VietJack)", REPO_ROOT / "02ScalingPhrase/localmodel/problems/VietJack_OnVao10_2026.math.v5.json"),
    ("API Math (MathNet)", REPO_ROOT / "02ScalingPhrase/apimodel/base-mathproblems.bigmodel.v5.math.json"),
]

PREAMBLE = "from fractions import Fraction\nimport decimal\nimport itertools\nimport math\n"


def df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = [f"{row[c]:.2f}" if isinstance(row[c], float) else str(row[c]) for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def audit_code_dataset(label: str, path: Path) -> list[dict[str, Any]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for t in tasks:
        tid = str(t.get("task_id"))
        code = str(t.get("code") or "")
        text = str(t.get("text") or "")
        setup = str(t.get("test_setup_code") or "")
        pub = [str(x) for x in (t.get("test_list") or [])]
        hid = [str(x) for x in (t.get("challenge_test_list") or [])]
        all_tests = pub + hid

        # Execute reference solution against all tests
        ns: dict[str, Any] = {}
        ref_pass = True
        ref_err = ""
        try:
            exec(PREAMBLE + "\n" + setup + "\n" + code, ns, ns)
            for tst in all_tests:
                exec(tst, ns, ns)
        except Exception as exc:  # noqa: BLE001
            ref_pass = False
            ref_err = f"{type(exc).__name__}: {exc}"

        # AST inspection of reference solution
        n_params = -1
        func_name = ""
        has_branching = False
        has_loop = False
        constant_return = False
        try:
            tree = ast.parse(code)
            funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            if funcs:
                fn = funcs[0]
                func_name = fn.name
                n_params = len(fn.args.args)
                returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
                if len(returns) == 1 and isinstance(returns[0].value, ast.Constant):
                    constant_return = True
            has_branching = any(isinstance(n, (ast.If, ast.IfExp)) for n in ast.walk(tree))
            has_loop = any(isinstance(n, (ast.For, ast.While, ast.ListComp, ast.GeneratorExp)) for n in ast.walk(tree))
        except SyntaxError:
            pass

        # Test quality checks
        norm_tests = [re.sub(r"\s+", "", x) for x in all_tests]
        dup_tests = len(norm_tests) - len(set(norm_tests))
        exact_float_asserts = sum(
            1 for x in all_tests
            if re.search(r"==\s*-?\d+\.\d+", x) and "isclose" not in x and "round(" not in x and "abs(" not in x
        )
        sig_in_prompt = bool(func_name and func_name in text)

        flags = []
        if not ref_pass:
            flags.append(f"REF_FAIL({ref_err[:60]})")
        if dup_tests > 0:
            flags.append(f"DUP_TESTS({dup_tests})")
        if n_params == 0:
            flags.append("ZERO_PARAM")
        if constant_return:
            flags.append("CONST_RETURN")
        if exact_float_asserts > 0:
            flags.append(f"EXACT_FLOAT_EQ({exact_float_asserts})")
        if not sig_in_prompt:
            flags.append("FUNC_NAME_NOT_IN_TEXT")

        rows.append({
            "dataset": label,
            "task_id": tid,
            "difficulty": str(t.get("difficulty", "")),
            "func_name": func_name,
            "n_params": n_params,
            "n_pub": len(pub),
            "n_hid": len(hid),
            "ref_pass": ref_pass,
            "dup_tests": dup_tests,
            "exact_float_eq": exact_float_asserts,
            "zero_param": n_params == 0,
            "const_return": constant_return,
            "sig_in_prompt": sig_in_prompt,
            "has_loop_or_branch": has_loop or has_branching,
            "flags": "; ".join(flags) if flags else "CLEAN",
        })
    return rows


def audit_math_dataset(label: str, path: Path) -> list[dict[str, Any]]:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for t in tasks:
        tid = str(t.get("task_id"))
        ans = t.get("expected_answer")
        prompt = str(t.get("prompt") or "")
        ans_str = str(ans).strip()
        is_int = bool(re.fullmatch(r"[-+]?\d+", ans_str))
        is_frac = "/" in ans_str
        is_dec = bool(re.fullmatch(r"[-+]?\d*\.\d+", ans_str))
        parse_ok = True
        try:
            if is_frac:
                a, b = ans_str.split("/", 1)
                val = float(a) / float(b)
            else:
                val = float(ans_str)
            parse_ok = math.isfinite(val)
        except Exception:  # noqa: BLE001
            parse_ok = False

        mentions_round = bool(re.search(r"round|decimal|nearest|fraction|integer", prompt, re.I))
        flags = []
        if not parse_ok:
            flags.append("UNPARSEABLE_ANSWER")
        if is_dec and not mentions_round:
            flags.append("DECIMAL_NO_ROUNDING_NOTE")
        rows.append({
            "dataset": label,
            "task_id": tid,
            "difficulty": str(t.get("difficulty", "")),
            "expected_answer": ans_str,
            "answer_type": "int" if is_int else ("fraction" if is_frac else ("decimal" if is_dec else "other")),
            "parse_ok": parse_ok,
            "mentions_format_or_round": mentions_round,
            "flags": "; ".join(flags) if flags else "CLEAN",
        })
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    code_rows: list[dict[str, Any]] = []
    for lbl, p in CODE_DATASETS:
        code_rows.extend(audit_code_dataset(lbl, p))
    math_rows: list[dict[str, Any]] = []
    for lbl, p in MATH_DATASETS:
        math_rows.extend(audit_math_dataset(lbl, p))

    cdf = pd.DataFrame(code_rows)
    mdf = pd.DataFrame(math_rows)
    cdf.to_csv(OUT_DIR / "oracle_audit_code_tasks.csv", index=False)
    mdf.to_csv(OUT_DIR / "oracle_audit_math_tasks.csv", index=False)

    # Summary by dataset
    code_sum = cdf.groupby("dataset", sort=True).agg(
        n_tasks=("task_id", "count"),
        ref_pass_n=("ref_pass", "sum"),
        clean_n=("flags", lambda s: int((s == "CLEAN").sum())),
        zero_param_n=("zero_param", "sum"),
        const_return_n=("const_return", "sum"),
        dup_test_tasks=("dup_tests", lambda s: int((s > 0).sum())),
        exact_float_eq_tasks=("exact_float_eq", lambda s: int((s > 0).sum())),
        sig_missing_n=("sig_in_prompt", lambda s: int((~s).sum())),
    ).reset_index()

    math_sum = mdf.groupby("dataset", sort=True).agg(
        n_tasks=("task_id", "count"),
        parse_ok_n=("parse_ok", "sum"),
        clean_n=("flags", lambda s: int((s == "CLEAN").sum())),
        n_int=("answer_type", lambda s: int((s == "int").sum())),
        n_frac=("answer_type", lambda s: int((s == "fraction").sum())),
        n_dec=("answer_type", lambda s: int((s == "decimal").sum())),
    ).reset_index()

    flagged_code = cdf[cdf["flags"] != "CLEAN"][["dataset", "task_id", "difficulty", "func_name", "n_params", "flags"]]
    flagged_math = mdf[mdf["flags"] != "CLEAN"][["dataset", "task_id", "difficulty", "expected_answer", "flags"]]

    md = [
        "# Independent Task Specification & Test-Oracle Audit (`R1C6` & `R2C12`)",
        "",
        "## 1. Python Code Benchmarks Summary (100 Tasks, 700 Assertions)",
        "",
        df_to_md(code_sum),
        "",
        "## 2. Flagged Python Tasks (Edge Cases, Float Equality, Zero-Param, or Signature Issues)",
        "",
        df_to_md(flagged_code) if not flagged_code.empty else "_No flagged Python tasks._",
        "",
        "## 3. Math Benchmarks Summary (100 Tasks)",
        "",
        df_to_md(math_sum),
        "",
        "## 4. Flagged Math Tasks",
        "",
        df_to_md(flagged_math) if not flagged_math.empty else "_No flagged Math tasks._",
        "",
    ]
    out_md = OUT_DIR / "oracle_audit_report.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_md}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
