#!/usr/bin/env python3
"""Analyze k=3 independent repeated generations (R1C3 / R2C14 / R2C15).

Reads repeated-run JSONL files from:
  - 14ImprovePhrase/results_api_repeated/{python,math}/*.jsonl
  - 14ImprovePhrase/results_local_repeated/*.jsonl  (downloaded from Kaggle)

Computes:
  1. Within-cell variability per model-task stratum:
     - flip / disagreement rate across k=3 repeats (cells where 0 < mean < 1)
     - exact agreement rate (all 3 pass or all 3 fail)
     - mean within-cell SD (sqrt of mean sample variance across repeats)
     - run-to-run SD of overall pass rate across rep_id 1..k
     - response-length (completion_tokens) and latency within-cell SD
  2. Re-estimated prompt contrasts (categories 2, 3, 4, 7, 13 vs baseline 1)
     with task-clustered standard errors, 95% CIs, and MDE_80 (k=3 vs single-rep k=1).

Outputs:
  - 14ImprovePhrase/analysis/repeated_runs_variability.csv
  - 14ImprovePhrase/analysis/repeated_runs_contrasts.csv
  - 14ImprovePhrase/analysis/repeated_runs_summary.md
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
API_REPEATED_DIR = SCRIPT_DIR / "results_api_repeated"
LOCAL_REPEATED_DIR = SCRIPT_DIR / "results_local_repeated"
OUT_DIR = SCRIPT_DIR / "analysis"

Z95 = 1.959963984540054
Z80 = 1.959963984540054 + 0.8416212335729143

CONTRASTS = [
    ("2", "JSON vs plaintext"),
    ("3", "XML vs plaintext"),
    ("4", "Role vs no role"),
    ("7", "Polite vs neutral"),
    ("13", "Aggressive vs neutral"),
]


def load_jsonl_records(paths: list[Path], regime: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(paths):
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("error") is not None:
                    continue
                dataset = str(rec.get("dataset", "")).lower()
                task_type = "code" if dataset in {"python", "code"} else "math"
                records.append(
                    {
                        "regime": regime,
                        "task_type": task_type,
                        "stratum": f"{'API' if regime == 'api' else 'Local'} {'Python' if task_type == 'code' else 'math'}",
                        "model": str(rec.get("model_label") or rec.get("model")),
                        "task_id": str(rec.get("task_id")),
                        "category_id": str(rec.get("category_id")),
                        "rep_id": int(rec.get("rep_id", 1)),
                        "passed": float(bool(rec.get("passed"))),
                        "duration_seconds": float(rec.get("duration_seconds") or 0.0),
                        "completion_tokens": float(rec.get("completion_tokens") or 0.0),
                    }
                )
    return records


def task_clustered_contrast(
    df: pd.DataFrame, base_cat: str, treat_cat: str
) -> dict[str, float]:
    """Compute paired task-clustered contrast (treat - base) across all models in df."""
    sub = df[df["category_id"].isin([base_cat, treat_cat])].copy()
    if sub.empty:
        return {
            "diff_pp": float("nan"),
            "se_pp": float("nan"),
            "ci_low_pp": float("nan"),
            "ci_high_pp": float("nan"),
            "mde80_pp": float("nan"),
            "n_tasks": 0,
        }
    piv = sub.groupby(["task_id", "category_id"])["passed"].mean().unstack()
    if base_cat not in piv.columns or treat_cat not in piv.columns:
        return {
            "diff_pp": float("nan"),
            "se_pp": float("nan"),
            "ci_low_pp": float("nan"),
            "ci_high_pp": float("nan"),
            "mde80_pp": float("nan"),
            "n_tasks": 0,
        }
    piv = piv.dropna(subset=[base_cat, treat_cat])
    diffs = (piv[treat_cat] - piv[base_cat]).to_numpy(dtype=float) * 100.0
    n_tasks = len(diffs)
    mean_diff = float(np.mean(diffs))
    se = float(np.std(diffs, ddof=1) / math.sqrt(n_tasks)) if n_tasks > 1 else float("nan")
    return {
        "diff_pp": mean_diff,
        "se_pp": se,
        "ci_low_pp": mean_diff - Z95 * se,
        "ci_high_pp": mean_diff + Z95 * se,
        "mde80_pp": Z80 * se,
        "n_tasks": n_tasks,
    }


def df_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append("NaN" if math.isnan(v) else f"{v:.2f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    api_files = list(API_REPEATED_DIR.glob("**/*.jsonl")) if API_REPEATED_DIR.exists() else []
    local_files = list(LOCAL_REPEATED_DIR.glob("**/*.jsonl")) if LOCAL_REPEATED_DIR.exists() else []

    records = load_jsonl_records(api_files, "api") + load_jsonl_records(local_files, "local")
    if not records:
        print("No repeated-run JSONL files found yet.")
        print(f"  Checked API dir  : {API_REPEATED_DIR}")
        print(f"  Checked Local dir: {LOCAL_REPEATED_DIR}")
        return

    df = pd.DataFrame(records)
    df = df.drop_duplicates(
        subset=["regime", "task_type", "model", "task_id", "category_id", "rep_id"],
        keep="last",
    )

    # 1. Within-cell variability table
    var_rows: list[dict[str, Any]] = []
    for (stratum, model), g in df.groupby(["stratum", "model"], sort=True):
        cells = g.groupby(["task_id", "category_id"]).agg(
            k=("passed", "count"),
            p_mean=("passed", "mean"),
            p_var=("passed", lambda s: float(np.var(s, ddof=1)) if len(s) > 1 else float("nan")),
            tok_sd=("completion_tokens", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else float("nan")),
            dur_sd=("duration_seconds", lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else float("nan")),
        )
        multi = cells[cells["k"] >= 2]
        flips = ((multi["p_mean"] > 0.0) & (multi["p_mean"] < 1.0)).mean() * 100.0 if len(multi) else float("nan")
        rep_means = g.groupby("rep_id")["passed"].mean() * 100.0
        var_rows.append(
            {
                "stratum": stratum,
                "model": model,
                "n_runs": len(g),
                "n_cells_multi": len(multi),
                "mean_k": float(multi["k"].mean()) if len(multi) else 0.0,
                "overall_pass_pct": float(g["passed"].mean() * 100.0),
                "rep_pass_sd_pp": float(rep_means.std(ddof=1)) if len(rep_means) > 1 else float("nan"),
                "within_cell_flip_pct": float(flips),
                "exact_agreement_pct": float(100.0 - flips) if not math.isnan(flips) else float("nan"),
                "mean_within_cell_sd_pp": float(np.sqrt(multi["p_var"].mean()) * 100.0) if len(multi) else float("nan"),
                "mean_tok_within_sd": float(multi["tok_sd"].mean()) if len(multi) else float("nan"),
                "mean_dur_within_sd_s": float(multi["dur_sd"].mean()) if len(multi) else float("nan"),
            }
        )

    var_df = pd.DataFrame(var_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    var_df.to_csv(OUT_DIR / "repeated_runs_variability.csv", index=False)

    # 2. Contrasts (k=3 pooled vs single-rep rep_id=1 precision comparison)
    contrast_rows: list[dict[str, Any]] = []
    for stratum, g in df.groupby("stratum", sort=True):
        g_rep1 = g[g["rep_id"] == 1]
        for cat_id, label in CONTRASTS:
            c_all = task_clustered_contrast(g, "1", cat_id)
            c_r1 = task_clustered_contrast(g_rep1, "1", cat_id)
            contrast_rows.append(
                {
                    "stratum": stratum,
                    "contrast": label,
                    "category_id": cat_id,
                    "n_tasks": c_all["n_tasks"],
                    "diff_k3_pp": round(c_all["diff_pp"], 3),
                    "se_k3_pp": round(c_all["se_pp"], 3),
                    "ci_low_k3_pp": round(c_all["ci_low_pp"], 3),
                    "ci_high_k3_pp": round(c_all["ci_high_pp"], 3),
                    "mde80_k3_pp": round(c_all["mde80_pp"], 3),
                    "diff_rep1_pp": round(c_r1["diff_pp"], 3),
                    "se_rep1_pp": round(c_r1["se_pp"], 3),
                    "mde80_rep1_pp": round(c_r1["mde80_pp"], 3),
                }
            )
    con_df = pd.DataFrame(contrast_rows)
    con_df.to_csv(OUT_DIR / "repeated_runs_contrasts.csv", index=False)

    # 3. Markdown summary
    md_lines = [
        "# Independent Repeated Generations (k = 3) Summary",
        "",
        f"Total valid runs loaded: **{len(df)}** across **{df['model'].nunique()}** model(s) and **{df['stratum'].nunique()}** stratum/strata.",
        "",
        "## 1. Within-Cell Variability",
        "",
        df_to_markdown(var_df),
        "",
        "## 2. Prompt Contrasts (k = 3 vs. Single-Repetition k = 1)",
        "",
        df_to_markdown(con_df),
        "",
    ]
    md_path = OUT_DIR / "repeated_runs_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote:\n  {OUT_DIR / 'repeated_runs_variability.csv'}\n  {OUT_DIR / 'repeated_runs_contrasts.csv'}\n  {md_path}")
    print("\n" + "\n".join(md_lines))


if __name__ == "__main__":
    main()
