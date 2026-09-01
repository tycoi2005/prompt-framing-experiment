from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
# This copy lives inside the results-analysis package itself, so the result
# files are directly under ROOT (the 10Paperv3 copy resolves RESULTS as
# PROJECT_ROOT / "02ScalingPhrase" / "results_analysis" instead).
RESULTS = ROOT
SOURCE_JSONL = RESULTS / "prompt_framing_experiment_results.jsonl"
CODE_TEMPLATE = RESULTS / "prompt_templates" / "prompt_matrix_prompt_template.09.csv"
MATH_TEMPLATE = RESULTS / "prompt_templates" / "prompt_matrix_prompt_template.09.math.csv"
OUT_DIR = ROOT / "analysis"


PROMPT_TERMS = [
    "tone_aggressive",
    "tone_polite",
    "role_vs_no_role",
    "format_json",
    "format_xml",
]

TERM_LABELS = {
    "tone_aggressive": "Aggressive tone",
    "tone_polite": "Polite tone",
    "role_vs_no_role": "Role framing",
    "format_json": "JSON wrapper",
    "format_xml": "XML wrapper",
}

MODEL_LABELS = {
    "deepseek-coder-6.7b-instruct": "DeepSeek Coder",
    "deepseek-coder-6.7b-instruct_1_50": "DeepSeek Coder",
    "gemma2-9b": "Gemma 2",
    "gemma2-9b_1_50": "Gemma 2",
    "gemma2:9b": "Gemma 2",
    "llama3.1-8b": "Llama 3.1",
    "llama3.1-8b_1_50": "Llama 3.1",
    "llama3.1:8b": "Llama 3.1",
    "mistral-7b-instruct": "Mistral",
    "mistral-7b-instruct_1_50": "Mistral",
    "mistral:7b-instruct": "Mistral",
    "nemotron-3-nano-4b": "Nemotron 3 Nano",
    "nemotron-3-nano-4b_1_50": "Nemotron 3 Nano",
    "nemotron-3-nano:4b": "Nemotron 3 Nano",
    "qwen2.5-7b": "Qwen2.5",
    "qwen2.5-7b_1_50": "Qwen2.5",
    "qwen2.5:7b": "Qwen2.5",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "gemini-flash": "Gemini Flash",
}


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def format_pp(value: float) -> str:
    return f"{value:+.1f} pp"


def p_value_two_proportion(success_a: int, n_a: int, success_b: int, n_b: int) -> float:
    if n_a == 0 or n_b == 0:
        return float("nan")
    p_a = success_a / n_a
    p_b = success_b / n_b
    pooled = (success_a + success_b) / (n_a + n_b)
    se = math.sqrt(max(pooled * (1 - pooled) * (1 / n_a + 1 / n_b), 0))
    if se == 0:
        return 1.0
    z = (p_b - p_a) / se
    return math.erfc(abs(z) / math.sqrt(2))


def load_prompt_metadata() -> dict[tuple[str, int], dict[str, str]]:
    metadata: dict[tuple[str, int], dict[str, str]] = {}
    for task_type, path in (("code", CODE_TEMPLATE), ("math", MATH_TEMPLATE)):
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                metadata[(task_type, int(row["ID"]))] = {
                    "tone": row["Tone"],
                    "role_binary": "role" if row["Role framing"] != "no role" else "no role",
                    "format": row["Format"],
                }
    return metadata


def parse_variant_and_base(row: dict[str, object]) -> tuple[int, str]:
    if row["modeltype"] == "api":
        return int(row["category_id"]), str(row["task_id"])

    task_id = str(row["task_id"])
    base_task, variant = task_id.rsplit("_", 1)
    return int(variant), base_task


def normalized_tokens(row: dict[str, object], field: str) -> int:
    if field in row and row[field] is not None:
        return int(row[field])
    raw_usage = row.get("raw_usage") or {}
    if isinstance(raw_usage, dict):
        return int(raw_usage.get(field, 0) or 0)
    return 0


def load_dataset() -> pd.DataFrame:
    metadata = load_prompt_metadata()
    rows: list[dict[str, object]] = []
    with SOURCE_JSONL.open() as handle:
        for line in handle:
            row = json.loads(line)
            task_type = str(row["task_type"])
            variant, base_task = parse_variant_and_base(row)
            prompt = metadata[(task_type, variant)]
            modelname = str(row["modelname"])
            response_text = str(row.get("response_text") or "")
            extracted_code = str(row.get("extracted_code") or "")
            rows.append(
                {
                    "modeltype": str(row["modeltype"]),
                    "task_type": task_type,
                    "task_label": "python" if task_type == "code" else "math",
                    "modelname": modelname,
                    "model_label": MODEL_LABELS.get(modelname, modelname),
                    "task_id": str(row["task_id"]),
                    "base_task": base_task,
                    "variant_id": variant,
                    "passed": bool(row["passed"]),
                    "passed_float": float(bool(row["passed"])),
                    "duration_seconds": float(row.get("duration_seconds") or 0),
                    "prompt_tokens": normalized_tokens(row, "prompt_tokens"),
                    "completion_tokens": normalized_tokens(row, "completion_tokens"),
                    "response_text": response_text,
                    "response_chars": len(response_text),
                    "extracted_code": extracted_code,
                    "code_chars": len(extracted_code),
                    "errors": row.get("errors"),
                    **prompt,
                }
            )

    df = pd.DataFrame(rows)
    df["extra_text_chars"] = (df["response_chars"] - df["code_chars"]).clip(lower=0)
    df["extra_text_ratio"] = np.where(
        df["response_chars"] > 0,
        df["extra_text_chars"] / df["response_chars"],
        np.nan,
    )
    df["has_code"] = (df["code_chars"] > 0).astype(int)
    df["result_only"] = 0
    code_mask = df["task_type"].eq("code")
    math_mask = df["task_type"].eq("math")
    df.loc[code_mask, "result_only"] = (
        (df.loc[code_mask, "has_code"] == 1)
        & (df.loc[code_mask, "extra_text_ratio"] < 0.15)
    ).astype(int)
    df.loc[math_mask, "result_only"] = (df.loc[math_mask, "response_chars"] < 50).astype(int)
    df["log_completion_tokens"] = np.log1p(df["completion_tokens"])
    df["log_duration"] = np.log1p(df["duration_seconds"])
    df["tone_aggressive"] = df["tone"].eq("aggressive").astype(float)
    df["tone_polite"] = df["tone"].eq("polite").astype(float)
    df["role_vs_no_role"] = df["role_binary"].eq("role").astype(float)
    df["format_json"] = df["format"].eq("json").astype(float)
    df["format_xml"] = df["format"].eq("xml").astype(float)
    return df


def fit_lpm(
    data: pd.DataFrame,
    outcome_col: str,
    regressor_cols: list[str],
    fe_cols: list[str],
) -> dict[str, dict[str, float]]:
    needed = [outcome_col, *regressor_cols, *fe_cols]
    work = data[needed].replace([np.inf, -np.inf], np.nan).dropna()
    if work.empty:
        return {}

    y = work[outcome_col].astype(float).to_numpy()
    x = work[regressor_cols].astype(float).copy()
    for col in fe_cols:
        dummies = pd.get_dummies(work[col].astype(str), prefix=col, drop_first=True, dtype=float)
        x = pd.concat([x, dummies], axis=1)
    x.insert(0, "Intercept", 1.0)

    x_values = x.to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(x_values, y, rcond=None)
    residuals = y - x_values @ beta
    dof = max(len(y) - x_values.shape[1], 1)
    sigma2 = float((residuals @ residuals) / dof)
    xtx_inv = np.linalg.pinv(x_values.T @ x_values)
    se = np.sqrt(np.clip(np.diag(xtx_inv) * sigma2, 0, np.inf))

    result: dict[str, dict[str, float]] = {}
    for term, coef, std_err in zip(x.columns, beta, se):
        if term not in regressor_cols:
            continue
        p_value = math.erfc(abs(coef / std_err) / math.sqrt(2)) if std_err > 0 else 1.0
        result[term] = {
            "coef": float(coef),
            "coef_pp": float(100 * coef),
            "std_err": float(std_err),
            "std_err_pp": float(100 * std_err),
            "p_value": float(p_value),
            "nobs": float(len(y)),
        }
    return result


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_data_integrity(df: pd.DataFrame) -> None:
    duplicate_keys = df.duplicated(["modeltype", "task_type", "modelname", "task_id", "variant_id"]).sum()
    empty_local = df[df["modeltype"].eq("local") & df["response_text"].eq("")]
    empty_api = df[df["modeltype"].eq("api") & df["response_text"].eq("")]
    rows = [
        {"check": "Total rows", "value": len(df)},
        {"check": "Local rows", "value": int(df["modeltype"].eq("local").sum())},
        {"check": "API rows", "value": int(df["modeltype"].eq("api").sum())},
        {"check": "Local result files implied", "value": 12},
        {"check": "API result files implied", "value": 4},
        {"check": "Duplicate full run keys", "value": int(duplicate_keys)},
        {"check": "Empty local responses", "value": len(empty_local)},
        {"check": "Empty API responses", "value": len(empty_api)},
    ]

    balanced_cells = 0
    unbalanced_cells = 0
    for _, group in df.groupby(["modeltype", "task_type", "modelname"]):
        variants_by_base = group.groupby("base_task")["variant_id"].nunique()
        if len(variants_by_base) == 50 and variants_by_base.eq(18).all():
            balanced_cells += 1
        else:
            unbalanced_cells += 1
    rows.extend(
        [
            {"check": "Balanced model-task cells", "value": balanced_cells},
            {"check": "Unbalanced model-task cells", "value": unbalanced_cells},
        ]
    )
    write_csv(OUT_DIR / "manuscript_data_integrity.csv", rows, ["check", "value"])


def write_model_performance(df: pd.DataFrame) -> None:
    rows = []
    for (modeltype, task_type, modelname), group in df.groupby(["modeltype", "task_type", "modelname"]):
        task_group = {
            ("local", "code"): "Local code",
            ("local", "math"): "Local math",
            ("api", "code"): "API Python",
            ("api", "math"): "API math",
        }[(modeltype, task_type)]
        rows.append(
            {
                "task_group": task_group,
                "modelname": modelname,
                "model_label": MODEL_LABELS.get(modelname, modelname),
                "n": len(group),
                "passes": int(group["passed"].sum()),
                "pass_rate_pct": 100 * group["passed"].mean(),
                "median_duration_seconds": group["duration_seconds"].median(),
                "mean_completion_tokens": group["completion_tokens"].mean(),
            }
        )
    rows.sort(key=lambda row: (row["task_group"], -float(row["pass_rate_pct"])))
    write_csv(
        OUT_DIR / "manuscript_model_performance.csv",
        rows,
        [
            "task_group",
            "modelname",
            "model_label",
            "n",
            "passes",
            "pass_rate_pct",
            "median_duration_seconds",
            "mean_completion_tokens",
        ],
    )


def contrast_rows(df: pd.DataFrame, modeltype: str, task_type: str) -> list[dict[str, object]]:
    specs = [
        ("tone", "neutral", "aggressive", "aggressive vs neutral"),
        ("tone", "neutral", "polite", "polite vs neutral"),
        ("role_binary", "no role", "role", "role vs none"),
        ("format", "plaintext", "json", "JSON vs plaintext"),
        ("format", "plaintext", "xml", "XML vs plaintext"),
    ]
    subset = df[df["modeltype"].eq(modeltype) & df["task_type"].eq(task_type)]
    rows = []
    for factor, baseline, level, contrast in specs:
        base = subset[subset[factor].eq(baseline)]
        alt = subset[subset[factor].eq(level)]
        p_value = p_value_two_proportion(
            int(base["passed"].sum()),
            len(base),
            int(alt["passed"].sum()),
            len(alt),
        )
        rows.append(
            {
                "modeltype": modeltype,
                "task_type": task_type,
                "task_group": {
                    ("local", "code"): "Local code",
                    ("local", "math"): "Local math",
                    ("api", "code"): "API Python",
                    ("api", "math"): "API math",
                }[(modeltype, task_type)],
                "factor": factor,
                "contrast": contrast,
                "baseline_n": len(base),
                "level_n": len(alt),
                "baseline_pass_rate": base["passed"].mean(),
                "level_pass_rate": alt["passed"].mean(),
                "pass_diff_pp": 100 * (alt["passed"].mean() - base["passed"].mean()),
                "p_value": p_value,
                "token_diff": alt["completion_tokens"].mean() - base["completion_tokens"].mean(),
                "duration_diff": alt["duration_seconds"].mean() - base["duration_seconds"].mean(),
            }
        )
    return rows


def write_prompt_contrasts(df: pd.DataFrame) -> None:
    rows = []
    for modeltype in ["local", "api"]:
        for task_type in ["code", "math"]:
            rows.extend(contrast_rows(df, modeltype, task_type))
    write_csv(
        OUT_DIR / "manuscript_prompt_contrasts.csv",
        rows,
        [
            "modeltype",
            "task_type",
            "task_group",
            "factor",
            "contrast",
            "baseline_n",
            "level_n",
            "baseline_pass_rate",
            "level_pass_rate",
            "pass_diff_pp",
            "p_value",
            "token_diff",
            "duration_diff",
        ],
    )


def write_behavior_effects(df: pd.DataFrame) -> None:
    rows = []
    local = df[df["modeltype"].eq("local")]
    fe_cols = ["modelname", "base_task"]
    outcomes = [
        ("log(tokens)", "log_completion_tokens", "percent"),
        ("result_only", "result_only", "pp"),
        ("log(duration)", "log_duration", "percent"),
    ]
    for task_type in ["code", "math"]:
        subset = local[local["task_type"].eq(task_type)]
        for metric_label, outcome_col, unit in outcomes:
            result = fit_lpm(subset, outcome_col, PROMPT_TERMS, fe_cols)
            for term in PROMPT_TERMS:
                rows.append(
                    {
                        "task_type": task_type,
                        "task_group": "Local code" if task_type == "code" else "Local math",
                        "metric": metric_label,
                        "factor": term,
                        "factor_label": TERM_LABELS[term],
                        "effect": result[term]["coef_pp"],
                        "p_value": result[term]["p_value"],
                        "significant_0_05": result[term]["p_value"] < 0.05,
                        "unit": unit,
                    }
                )
    write_csv(
        OUT_DIR / "manuscript_behavior_effects.csv",
        rows,
        ["task_type", "task_group", "metric", "factor", "factor_label", "effect", "p_value", "significant_0_05", "unit"],
    )


def write_mediation(df: pd.DataFrame) -> None:
    rows = []
    local = df[df["modeltype"].eq("local")]
    fe_cols = ["modelname", "base_task"]
    specs = {
        "+tokens": ["log_completion_tokens"],
        "+res_only": ["result_only"],
        "+duration": ["log_duration"],
        "+all3": ["log_completion_tokens", "result_only", "log_duration"],
    }
    for task_type in ["code", "math"]:
        subset = local[local["task_type"].eq(task_type)]
        total_res = fit_lpm(subset, "passed_float", PROMPT_TERMS, fe_cols)
        for term in PROMPT_TERMS:
            total_coef = total_res[term]["coef"]
            row: dict[str, object] = {
                "task_type": task_type,
                "task_group": "Local code" if task_type == "code" else "Local math",
                "factor": term,
                "factor_label": TERM_LABELS[term],
                "total_pp": total_res[term]["coef_pp"],
                "total_p": total_res[term]["p_value"],
            }
            for spec_name, controls in specs.items():
                controlled_res = fit_lpm(subset, "passed_float", [*PROMPT_TERMS, *controls], fe_cols)
                controlled = controlled_res[term]["coef"]
                indirect = total_coef - controlled
                row[f"{spec_name}_pp"] = controlled_res[term]["coef_pp"]
                row[f"{spec_name}_prop"] = indirect / total_coef if abs(total_coef) > 1e-10 else ""
            rows.append(row)
    write_csv(
        OUT_DIR / "manuscript_mediation_decomposition.csv",
        rows,
        [
            "task_type",
            "task_group",
            "factor",
            "factor_label",
            "total_pp",
            "total_p",
            "+tokens_pp",
            "+tokens_prop",
            "+res_only_pp",
            "+res_only_prop",
            "+duration_pp",
            "+duration_prop",
            "+all3_pp",
            "+all3_prop",
        ],
    )


def write_dominant_sensitivity(df: pd.DataFrame) -> None:
    specs = [
        ("Local, no Nemotron", "local", "code", "nemotron-3-nano-4b"),
        ("Local, no Nemotron", "local", "math", "nemotron-3-nano-4b"),
        ("API, no DeepSeek", "api", "math", "deepseek-v4-flash"),
        ("API, no DeepSeek", "api", "code", "deepseek-v4-flash"),
    ]
    rows = []
    for label, modeltype, task_type, excluded_model in specs:
        subset = df[df["modeltype"].eq(modeltype) & df["task_type"].eq(task_type)]
        without = subset[~subset["modelname"].eq(excluded_model)]
        rows.append(
            {
                "sensitivity_dataset": label,
                "task_kind": "python" if task_type == "code" else "math",
                "full_avg_pct": 100 * subset["passed"].mean(),
                "without_dominant_pct": 100 * without["passed"].mean(),
                "excluded_model": excluded_model,
            }
        )
    write_csv(
        OUT_DIR / "manuscript_dominant_sensitivity.csv",
        rows,
        ["sensitivity_dataset", "task_kind", "full_avg_pct", "without_dominant_pct", "excluded_model"],
    )


def write_failure_examples(df: pd.DataFrame) -> None:
    rows: list[dict[str, object]] = []
    nemotron_empty = df[
        df["modelname"].eq("nemotron-3-nano-4b_1_50")
        & df["task_type"].eq("code")
        & df["response_text"].eq("")
    ].head(1)
    if not nemotron_empty.empty:
        row = nemotron_empty.iloc[0]
        rows.append(
            {
                "example": "Nemotron empty code response",
                "modelname": row["modelname"],
                "task_id": row["task_id"],
                "variant_id": row["variant_id"],
                "format": row["format"],
                "passed": row["passed"],
                "evidence": "empty response_text; evaluator errors include No code extracted in source JSONL",
            }
        )

    qwen_code = df[
        df["modelname"].eq("qwen2.5-7b_1_50")
        & df["task_type"].eq("code")
        & df["passed"].eq(False)
        & df["errors"].astype(str).str.contains("not defined", regex=False)
    ].head(1)
    if not qwen_code.empty:
        row = qwen_code.iloc[0]
        rows.append(
            {
                "example": "Qwen code name-resolution failure",
                "modelname": row["modelname"],
                "task_id": row["task_id"],
                "variant_id": row["variant_id"],
                "format": row["format"],
                "passed": row["passed"],
                "evidence": str(row["errors"])[:240],
            }
        )

    qwen_math = df[
        df["modelname"].eq("qwen2.5-7b_1_50")
        & df["task_type"].eq("math")
        & df["task_id"].eq("math_001_2")
    ].head(1)
    if not qwen_math.empty:
        row = qwen_math.iloc[0]
        rows.append(
            {
                "example": "Qwen math compact wrong answer",
                "modelname": row["modelname"],
                "task_id": row["task_id"],
                "variant_id": row["variant_id"],
                "format": row["format"],
                "passed": row["passed"],
                "evidence": "JSON prompt variant returns response_text '6' where expected answer is 12.0 in source JSONL",
            }
        )
    write_csv(
        OUT_DIR / "manuscript_failure_examples.csv",
        rows,
        ["example", "modelname", "task_id", "variant_id", "format", "passed", "evidence"],
    )


def write_markdown_summary() -> None:
    model_perf = pd.read_csv(OUT_DIR / "manuscript_model_performance.csv")
    behavior = pd.read_csv(OUT_DIR / "manuscript_behavior_effects.csv")
    mediation = pd.read_csv(OUT_DIR / "manuscript_mediation_decomposition.csv")
    sensitivity = pd.read_csv(OUT_DIR / "manuscript_dominant_sensitivity.csv")
    contrasts = pd.read_csv(OUT_DIR / "manuscript_prompt_contrasts.csv")

    lines = [
        "# Recomputed Manuscript Tables",
        "",
        f"Source data: `{SOURCE_JSONL.relative_to(PROJECT_ROOT)}`.",
        "",
        "Generated by `06Paperv2/scripts/recompute_manuscript_tables.py`.",
        "",
        "## Headline Ranges",
        "",
        "| Group | Minimum | Maximum |",
        "|---|---:|---:|",
    ]
    for group_name, group in model_perf.groupby("task_group", sort=False):
        minimum = group.sort_values("pass_rate_pct").iloc[0]
        maximum = group.sort_values("pass_rate_pct").iloc[-1]
        lines.append(
            f"| {group_name} | {minimum.model_label}, {format_percent(minimum.pass_rate_pct)} | {maximum.model_label}, {format_percent(maximum.pass_rate_pct)} |"
        )

    lines.extend(["", "## Selected Prompt Contrasts", "", "| Group | Contrast | Pass diff | p | Token diff | Duration diff |", "|---|---|---:|---:|---:|---:|"])
    selected_contrasts = contrasts[
        ((contrasts.task_group == "API Python") & contrasts.contrast.isin(["JSON vs plaintext", "XML vs plaintext"]))
        | ((contrasts.task_group == "Local math") & contrasts.contrast.isin(["JSON vs plaintext", "XML vs plaintext"]))
        | ((contrasts.task_group == "API math") & contrasts.contrast.eq("role vs none"))
    ]
    for row in selected_contrasts.itertuples():
        lines.append(
            f"| {row.task_group} | {row.contrast} | {format_pp(row.pass_diff_pp)} | {row.p_value:.3f} | {row.token_diff:+.0f} | {row.duration_diff:+.2f}s |"
        )

    lines.extend(["", "## Behavior Effects", "", "| Group | Factor | Tokens | Result-only | Duration |", "|---|---|---:|---:|---:|"])
    for task_group in ["Local code", "Local math"]:
        for factor in PROMPT_TERMS:
            subset = behavior[(behavior.task_group == task_group) & (behavior.factor == factor)]
            values = {row.metric: row.effect for row in subset.itertuples()}
            lines.append(
                f"| {task_group} | {TERM_LABELS[factor]} | {values['log(tokens)']:+.2f}% | {values['result_only']:+.2f} pp | {values['log(duration)']:+.2f}% |"
            )

    lines.extend(["", "## Mediation Decomposition", "", "| Group | Factor | Total | After all behavior controls |", "|---|---|---:|---:|"])
    for row in mediation.itertuples():
        lines.append(f"| {row.task_group} | {row.factor_label} | {row.total_pp:+.2f} pp | {getattr(row, '_13'):+.2f} pp |")

    lines.extend(["", "## Dominant-Model Sensitivity", "", "| Dataset | Task | Full avg. | Without dominant |", "|---|---|---:|---:|"])
    for row in sensitivity.itertuples():
        lines.append(
            f"| {row.sensitivity_dataset} | {row.task_kind} | {format_percent(row.full_avg_pct)} | {format_percent(row.without_dominant_pct)} |"
        )

    (ROOT / "manuscript_table_audit.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = load_dataset()
    write_data_integrity(df)
    write_model_performance(df)
    write_prompt_contrasts(df)
    write_behavior_effects(df)
    write_mediation(df)
    write_dominant_sensitivity(df)
    write_failure_examples(df)
    write_markdown_summary()


if __name__ == "__main__":
    main()
