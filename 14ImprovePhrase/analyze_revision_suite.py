#!/usr/bin/env python3
"""Unified analyzer for all 4 revision experiment suites (R1C4, R2C5/R2C14, R2C10, R2C7).

Reads:
  - 14ImprovePhrase/results_revision/{api,local}/*.jsonl
  - 14ImprovePhrase/results_api_repeated/python/*.repeated.jsonl   (for R2C5/14 baseline comparison)
  - 14ImprovePhrase/results_local_repeated/*.code.repeated_k3.jsonl (for R2C10 & R2C5/14 comparison)
  - 10Paperv3/analysis/manuscript_pipeline_replay.csv               (for R1C4 simulated vs measured)

Writes:
  - 14ImprovePhrase/analysis/revision_suite_report.md
  - 14ImprovePhrase/analysis/r1c4_measured_pipeline.csv
  - 14ImprovePhrase/analysis/r2c5_r2c14_paraphrase.csv
  - 14ImprovePhrase/analysis/r2c10_shared_task.csv
  - 14ImprovePhrase/analysis/r2c7_se_bench.csv
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REV_DIR = SCRIPT_DIR / "results_revision"
LOCAL_K3_DIR = SCRIPT_DIR / "results_local_repeated"
API_K3_DIR = SCRIPT_DIR / "results_api_repeated" / "python"
OUT_DIR = SCRIPT_DIR / "analysis"
SIM_REPLAY_CSV = REPO_ROOT / "10Paperv3" / "analysis" / "manuscript_pipeline_replay.csv"


def df_to_md(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No data yet._"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            vals.append("NaN" if isinstance(v, float) and math.isnan(v) else (f"{v:.2f}" if isinstance(v, float) else str(v)))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def load_suite(pattern: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for p in sorted(REV_DIR.glob(f"**/*{pattern}*.jsonl")):
        with p.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("api_error") is None:
                    rows.append(rec)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["regime", "model_label", "item_key"], keep="last")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = ["# Unified Revision Experiment Suite Report (`R1C4`, `R2C5/R2C14`, `R2C10`, `R2C7`)", ""]

    # 1. R1C4 Live Pipeline
    df_pipe = load_suite("r1c4_pipeline")
    if not df_pipe.empty:
        rows = []
        for (regime, model, policy), g in df_pipe.groupby(["regime", "model_label", "policy_label"], sort=True):
            r0 = float(g["passed_r0"].mean() * 100)
            r1 = float(g["passed_r1"].mean() * 100)
            r2 = float(g["passed_r2"].mean() * 100)
            parse_fail = float(g["initial_stage"].isin(["empty_response", "parse_fail", "syntax_fail"]).mean() * 100)
            rows.append({
                "regime": regime,
                "model": model,
                "policy": policy,
                "n": len(g),
                "measured_r0_pct": r0,
                "measured_r1_pct": r1,
                "measured_r2_pct": r2,
                "gain_pp": r2 - r0,
                "init_parse_syntax_fail_pct": parse_fail,
                "calls_per_1k": float(g["attempts_used"].mean() * 1000),
                "mean_total_comp_tok": float(g["total_completion_tokens"].mean()),
                "mean_llm_s": float(g["llm_total_ms"].mean() / 1000),
                "mean_consumer_ms": float(g["consumer_total_ms"].mean()),
            })
        p_df = pd.DataFrame(rows)
        p_df.to_csv(OUT_DIR / "r1c4_measured_pipeline.csv", index=False)
        md += ["## 1. `R1C4` — Measured Live End-to-End Pipeline (Real Retries)", "", df_to_md(p_df), ""]
        if SIM_REPLAY_CSV.exists():
            sim = pd.read_csv(SIM_REPLAY_CSV)
            sim_ov = sim[(sim["factor"] == "overall") & (sim["task_group"].isin(["API Python", "Local code"]))][
                ["task_group", "end_to_end_r0", "end_to_end_r1", "end_to_end_r2", "calls_per_1k_r2"]
            ].copy()
            for col in ["end_to_end_r0", "end_to_end_r1", "end_to_end_r2"]:
                sim_ov[col] = sim_ov[col] * 100.0
            md += ["### Reference: Earlier Simulated Offline Replay (Clearly Separated)", "", df_to_md(sim_ov), ""]
    else:
        md += ["## 1. `R1C4` — Measured Live End-to-End Pipeline", "", "_No data yet._", ""]

    # 2. R2C5 / R2C14 Paraphrase & Length-Matched Neutral Controls
    df_para = load_suite("r2c5_r2c14_paraphrase")
    if not df_para.empty:
        p2_df = (
            df_para.groupby(["regime", "model_label", "variant"], sort=True)
            .agg(
                n=("passed", "count"),
                pass_pct=("passed", lambda s: float(s.mean() * 100)),
                mean_prompt_tok=("prompt_tokens", "mean"),
                mean_comp_tok=("completion_tokens", "mean"),
                mean_llm_s=("llm_ms", lambda s: float(s.mean() / 1000)),
            )
            .reset_index()
        )
        p2_df.to_csv(OUT_DIR / "r2c5_r2c14_paraphrase.csv", index=False)
        md += ["## 2. `R2C5 / R2C14` — Neutral Paraphrase & Length-Matched Neutral Controls", "", df_to_md(p2_df), ""]
    else:
        md += ["## 2. `R2C5 / R2C14` — Neutral Paraphrase & Length-Matched Neutral Controls", "", "_No data yet._", ""]

    # 3. R2C10 Shared-Task Comparison (API on TOANMATH vs Local on exact same tasks)
    df_sh = load_suite("r2c10_shared_task")
    if not df_sh.empty:
        shared_tids = set(df_sh["task_id"].astype(str))
        sh_rows = []
        for (model, policy), g in df_sh.groupby(["model_label", "policy_label"], sort=True):
            sh_rows.append({"regime": "API (shared TOANMATH)", "model": model, "policy": policy, "n": len(g), "pass_pct": float(g["passed"].mean() * 100), "mean_comp_tok": float(g["completion_tokens"].mean())})
        # Pull matching Local rep_id=1 rows on the exact same shared_tids
        cat_map = {"1": "neutral_plaintext", "3": "neutral_xml", "7": "polite_plaintext"}
        for p in sorted(LOCAL_K3_DIR.glob("*.code.repeated_k3.jsonl")):
            recs = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
            sub = [r for r in recs if r.get("error") is None and int(r.get("rep_id", 0)) == 1 and str(r["task_id"]) in shared_tids and str(r["category_id"]) in cat_map]
            if not sub:
                continue
            sdf = pd.DataFrame(sub)
            sdf["policy_label"] = sdf["category_id"].astype(str).map(cat_map)
            for (model, policy), g in sdf.groupby(["model_label", "policy_label"], sort=True):
                sh_rows.append({"regime": "Local (reused TOANMATH)", "model": model, "policy": policy, "n": len(g), "pass_pct": float(g["passed"].mean() * 100), "mean_comp_tok": float(g["completion_tokens"].mean())})
        sh_df = pd.DataFrame(sh_rows)
        sh_df.to_csv(OUT_DIR / "r2c10_shared_task.csv", index=False)
        md += ["## 3. `R2C10` — Shared-Task Cross-Regime Comparison (Same TOANMATH Tasks)", "", df_to_md(sh_df), ""]
    else:
        md += ["## 3. `R2C10` — Shared-Task Cross-Regime Comparison", "", "_No data yet._", ""]

    # 4. R2C7 Non-Math SE Benchmark
    df_se = load_suite("r2c7_se_bench")
    if not df_se.empty:
        se_df = (
            df_se.groupby(["regime", "model_label", "policy_label"], sort=True)
            .agg(
                n=("passed", "count"),
                pass_pct=("passed", lambda s: float(s.mean() * 100)),
                mean_comp_tok=("completion_tokens", "mean"),
                mean_llm_s=("llm_ms", lambda s: float(s.mean() / 1000)),
            )
            .reset_index()
        )
        se_df.to_csv(OUT_DIR / "r2c7_se_bench.csv", index=False)
        md += ["## 4. `R2C7` — Independent Non-Math SE Coding Benchmark (15 Tasks)", "", df_to_md(se_df), ""]
    else:
        md += ["## 4. `R2C7` — Independent Non-Math SE Coding Benchmark", "", "_No data yet._", ""]

    out_md = OUT_DIR / "revision_suite_report.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_md}")
    print("\n".join(md))


if __name__ == "__main__":
    main()
