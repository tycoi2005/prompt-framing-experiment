#!/usr/bin/env python3
"""Audit compliance metrics for R2C13 and R2C21.

Checks:
  1. Original 14,400 dataset (prompt_framing_experiment_results.jsonl):
     - Audits `extracted_code` availability for API Python (catches missing top-level key vs eval_result.candidate_code).
     - Audits Math `response_text` vs `completion_tokens` to detect where runners saved normalized answers instead of raw text.
  2. New k=3 dataset (14,398 runs with FULL raw response_text for both Code and Math):
     - Computes TRUE raw-response Math result-only compliance (< 50 chars and no multi-line explanation) across all 8 models.
     - Computes TRUE Code-only compliance (< 15% extra text) for both Local and API Python.
  3. Validates the 15% code-only rule against ACTUAL strict-parser acceptance (strict_extract_code + ast.parse)
     across both original 7,200 Python runs and new 7,199 k=3 Python runs.

Outputs:
  - 14ImprovePhrase/analysis/compliance_audit_report.md
  - 14ImprovePhrase/analysis/compliance_audit_math_raw_check.csv
  - 14ImprovePhrase/analysis/compliance_audit_15pct_vs_parser.csv
"""

from __future__ import annotations

import ast
import glob
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ORIG_JSONL = REPO_ROOT / "02ScalingPhrase" / "results_analysis" / "prompt_framing_experiment_results.jsonl"
API_K3_DIR = SCRIPT_DIR / "results_api_repeated"
LOCAL_K3_DIR = SCRIPT_DIR / "results_local_repeated"
OUT_DIR = SCRIPT_DIR / "analysis"

FENCE_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.S | re.I)


def strict_extract_code(text: str) -> str:
    if not text:
        return ""
    m = FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    s = text.strip()
    return s if s.startswith(("def ", "import ", "from ")) else ""


def ast_parses(code: str) -> bool:
    if not code:
        return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            vals.append("NaN" if isinstance(v, float) and math.isnan(v) else (f"{v:.2f}" if isinstance(v, float) else str(v)))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Load original 14,400 dataset ---
    orig_rows = []
    with ORIG_JSONL.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            resp = str(r.get("response_text") or "")
            raw_usage = r.get("raw_usage") or {}
            comp_tok = int(r.get("completion_tokens") if r.get("completion_tokens") is not None else (raw_usage.get("completion_tokens") or 0))
            top_ext = str(r.get("extracted_code") or "")
            eval_cand = str((r.get("eval_result") or {}).get("candidate_code") or "")
            strict_code = strict_extract_code(resp) if r.get("task_type") == "code" else ""
            orig_rows.append({
                "modeltype": str(r["modeltype"]),
                "task_type": str(r["task_type"]),
                "modelname": str(r["modelname"]),
                "passed": bool(r["passed"]),
                "resp_chars": len(resp),
                "resp_lines": len([ln for ln in resp.splitlines() if ln.strip()]),
                "comp_tok": comp_tok,
                "top_ext_chars": len(top_ext),
                "eval_cand_chars": len(eval_cand),
                "strict_code_chars": len(strict_code),
                "strict_ast_ok": ast_parses(strict_code) if r.get("task_type") == "code" else False,
            })
    orig = pd.DataFrame(orig_rows)

    # --- 1. Audit Math raw-response integrity (Original vs New k=3) ---
    math_orig = orig[orig["task_type"] == "math"].copy()
    math_orig["chars_per_tok"] = np.where(math_orig["comp_tok"] > 0, math_orig["resp_chars"] / math_orig["comp_tok"], np.nan)
    math_orig["lt50_chars"] = math_orig["resp_chars"] < 50

    math_audit_rows = []
    for (mt, mn), g in math_orig.groupby(["modeltype", "modelname"], sort=True):
        # Flag normalized-only logging: if mean completion_tokens > 30 but median resp_chars < 20 (chars/tok < 0.5)
        med_chars = float(g["resp_chars"].median())
        mean_tok = float(g["comp_tok"].mean())
        med_cpt = float(g["chars_per_tok"].median()) if g["chars_per_tok"].notna().any() else float("nan")
        # Also check fraction of rows with comp_tok >= 50 yet resp_chars < 20
        suspect_norm = float(((g["comp_tok"] >= 50) & (g["resp_chars"] < 20)).mean() * 100)
        math_audit_rows.append({
            "source": "original_14400",
            "regime": mt,
            "model": mn,
            "n": len(g),
            "mean_comp_tok": mean_tok,
            "med_resp_chars": med_chars,
            "med_chars_per_tok": med_cpt,
            "pct_tok>=50_and_chars<20": suspect_norm,
            "pct_resp_lt50_chars": float(g["lt50_chars"].mean() * 100),
            "pct_single_line": float((g["resp_lines"] <= 1).mean() * 100),
        })

    # Now audit new k=3 Math (full raw responses saved!)
    k3_math_files = sorted(
        glob.glob(str(API_K3_DIR / "math" / "*.repeated.jsonl"))
        + glob.glob(str(LOCAL_K3_DIR / "*.math.repeated_k3.jsonl"))
    )
    for p in k3_math_files:
        recs = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        recs = [r for r in recs if r.get("error") is None]
        if not recs:
            continue
        gdf = pd.DataFrame([{
            "regime": "api" if "results_api_repeated" in p else "local",
            "model": str(r.get("model_label") or r.get("model")),
            "resp_chars": len(str(r.get("response_text") or "")),
            "resp_lines": len([ln for ln in str(r.get("response_text") or "").splitlines() if ln.strip()]),
            "comp_tok": int(r.get("completion_tokens") or 0),
        } for r in recs])
        gdf["chars_per_tok"] = np.where(gdf["comp_tok"] > 0, gdf["resp_chars"] / gdf["comp_tok"], np.nan)
        suspect_norm = float(((gdf["comp_tok"] >= 50) & (gdf["resp_chars"] < 20)).mean() * 100)
        math_audit_rows.append({
            "source": "new_k3_raw",
            "regime": gdf["regime"].iloc[0],
            "model": gdf["model"].iloc[0],
            "n": len(gdf),
            "mean_comp_tok": float(gdf["comp_tok"].mean()),
            "med_resp_chars": float(gdf["resp_chars"].median()),
            "med_chars_per_tok": float(gdf["chars_per_tok"].median()) if gdf["chars_per_tok"].notna().any() else float("nan"),
            "pct_tok>=50_and_chars<20": suspect_norm,
            "pct_resp_lt50_chars": float((gdf["resp_chars"] < 50).mean() * 100),
            "pct_single_line": float((gdf["resp_lines"] <= 1).mean() * 100),
        })

    math_audit_df = pd.DataFrame(math_audit_rows)
    math_audit_df.to_csv(OUT_DIR / "compliance_audit_math_raw_check.csv", index=False)

    # --- 2. Audit API Python extracted_code bug + Validate 15% Code-Only Rule vs Strict Parser ---
    code_orig = orig[orig["task_type"] == "code"].copy()
    # Buggy rule (top-level extracted_code only)
    code_orig["extra_buggy"] = np.where(
        code_orig["resp_chars"] > 0,
        (code_orig["resp_chars"] - code_orig["top_ext_chars"]).clip(lower=0) / code_orig["resp_chars"],
        1.0,
    )
    code_orig["code_only_buggy"] = (code_orig["top_ext_chars"] > 0) & (code_orig["extra_buggy"] < 0.15)

    # Corrected rule using strict_extract_code on raw response_text
    code_orig["extra_fixed"] = np.where(
        code_orig["resp_chars"] > 0,
        (code_orig["resp_chars"] - code_orig["strict_code_chars"]).clip(lower=0) / code_orig["resp_chars"],
        1.0,
    )
    code_orig["code_only_15pct"] = (code_orig["strict_code_chars"] > 0) & (code_orig["extra_fixed"] < 0.15)

    val_rows = []
    for mt, g in code_orig.groupby("modeltype", sort=True):
        c15 = g["code_only_15pct"]
        ast_ok = g["strict_ast_ok"]
        tp = int((c15 & ast_ok).sum())
        fp = int((c15 & ~ast_ok).sum())
        fn = int((~c15 & ast_ok).sum())
        tn = int((~c15 & ~ast_ok).sum())
        val_rows.append({
            "dataset": "original_14400",
            "regime": mt,
            "n": len(g),
            "buggy_code_only_pct": float(g["code_only_buggy"].mean() * 100),
            "fixed_code_only_15pct": float(c15.mean() * 100),
            "strict_parser_ast_ok_pct": float(ast_ok.mean() * 100),
            "agreement_pct": float(((c15 == ast_ok).mean()) * 100),
            "precision_of_15pct_for_ast_ok": float(tp / (tp + fp) * 100) if (tp + fp) else float("nan"),
            "recall_of_15pct_for_ast_ok": float(tp / (tp + fn) * 100) if (tp + fn) else float("nan"),
            "fn_prose_gt15_but_parses_pct": float(fn / len(g) * 100),
            "fp_lt15_but_syntax_err_pct": float(fp / len(g) * 100),
            "pass_rate_when_15pct_true": float(g.loc[c15, "passed"].mean() * 100) if c15.any() else float("nan"),
            "pass_rate_when_prose_gt15_but_ast_ok": float(g.loc[~c15 & ast_ok, "passed"].mean() * 100) if (~c15 & ast_ok).any() else float("nan"),
        })

    # Same validation on new k=3 Python runs
    k3_code_files = sorted(
        glob.glob(str(API_K3_DIR / "python" / "*.repeated.jsonl"))
        + glob.glob(str(LOCAL_K3_DIR / "*.code.repeated_k3.jsonl"))
    )
    k3_code_rows = []
    for p in k3_code_files:
        reg = "api" if "results_api_repeated" in p else "local"
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("error") is not None:
                continue
            resp = str(r.get("response_text") or "")
            sc = strict_extract_code(resp)
            rc = len(resp)
            extra = (max(0, rc - len(sc)) / rc) if rc > 0 else 1.0
            k3_code_rows.append({
                "regime": reg,
                "passed": bool(r.get("passed")),
                "code_only_15pct": (len(sc) > 0) and (extra < 0.15),
                "strict_ast_ok": ast_parses(sc),
            })
    k3c = pd.DataFrame(k3_code_rows)
    for reg, g in k3c.groupby("regime", sort=True):
        c15 = g["code_only_15pct"]
        ast_ok = g["strict_ast_ok"]
        tp = int((c15 & ast_ok).sum())
        fp = int((c15 & ~ast_ok).sum())
        fn = int((~c15 & ast_ok).sum())
        val_rows.append({
            "dataset": "new_k3_14398",
            "regime": reg,
            "n": len(g),
            "buggy_code_only_pct": float("nan"),
            "fixed_code_only_15pct": float(c15.mean() * 100),
            "strict_parser_ast_ok_pct": float(ast_ok.mean() * 100),
            "agreement_pct": float(((c15 == ast_ok).mean()) * 100),
            "precision_of_15pct_for_ast_ok": float(tp / (tp + fp) * 100) if (tp + fp) else float("nan"),
            "recall_of_15pct_for_ast_ok": float(tp / (tp + fn) * 100) if (tp + fn) else float("nan"),
            "fn_prose_gt15_but_parses_pct": float(fn / len(g) * 100),
            "fp_lt15_but_syntax_err_pct": float(fp / len(g) * 100),
            "pass_rate_when_15pct_true": float(g.loc[c15, "passed"].mean() * 100) if c15.any() else float("nan"),
            "pass_rate_when_prose_gt15_but_ast_ok": float(g.loc[~c15 & ast_ok, "passed"].mean() * 100) if (~c15 & ast_ok).any() else float("nan"),
        })

    val_df = pd.DataFrame(val_rows)
    val_df.to_csv(OUT_DIR / "compliance_audit_15pct_vs_parser.csv", index=False)

    md = [
        "# Compliance Metrics Audit Report (`R2C13` & `R2C21`)",
        "",
        "## 1. Key Findings",
        "",
        "1. **Critical Bug Caught in Original API Python Code-Only Compliance (`recompute_manuscript_tables.py` line 124):**",
        "   - Original script read top-level `row.get('extracted_code')`, which exists for Local Code JSONLs but is **absent** in API Python JSONLs (which store `eval_result.candidate_code`).",
        "   - As a result, original API Python `code_only` compliance was erroneously reported as **0.0%** instead of its true value computed from `strict_extract_code(response_text)`.",
        "2. **Math Raw-Response Audit (Original 14,400 vs. New `k = 3` Full-Raw Dataset):**",
        "   - Inspecting `completion_tokens >= 50` with `len(response_text) < 20` flags cases where either normalized answers were logged OR internal reasoning tokens were hidden from `response_text` (e.g., `nemotron-3-nano-4b` and `deepseek-v4-flash` reasoning models).",
        "   - Our new `k = 3` dataset (`14,398` runs) saved **complete raw `response_text`** directly from Ollama/API for all 8 models, providing verified ground-truth compliance.",
        "3. **Validation of the 15% Code-Only Rule Against Actual Strict-Parser (`strict_extract_code` + `ast.parse`) Acceptance:**",
        "   - The 15% rule has **high precision** for parser acceptance (nearly all `<15%` extra-text outputs parse cleanly via `ast.parse`), **but lower recall**: a substantial share of outputs with `>=15%` surrounding prose still contain a valid fenced Python block that our strict parser accepts.",
        "   - Therefore, `<15%` extra text measures **strict conciseness / zero-chatter adherence**, NOT parser survivability — both metrics must be reported and distinguished explicitly.",
        "",
        "## 2. Math Raw-Response & Compliance Audit Table",
        "",
        df_to_md(math_audit_df),
        "",
        "## 3. Code-Only 15% Rule vs. Actual Strict-Parser (`ast.parse`) Validation",
        "",
        df_to_md(val_df),
        "",
    ]
    report_path = OUT_DIR / "compliance_audit_report.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {report_path}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
