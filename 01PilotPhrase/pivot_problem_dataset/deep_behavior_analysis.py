from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parent
PROBLEMS_PATH = ROOT / "problems.csv"
PROMPT_MATRIX_PATH = ROOT / "prompt_matrix_prompt_template.08.csv"
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = ROOT / "analysis_outputs" / "deep_behavior"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> pd.DataFrame:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["source_file"] = path.name
            rows.append(row)
    return pd.DataFrame(rows)


def parse_result_task_id(value: object) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)_(\d+)", str(value))
    if not match:
        raise ValueError(f"Unexpected result task_id format: {value!r}")
    return int(match.group(1)), int(match.group(2))


def short_model_name(source_file: str, model_value: object = None) -> str:
    if source_file.endswith("_final.jsonl"):
        return source_file.removesuffix("_final.jsonl")
    if model_value is not None:
        return str(model_value).replace(":", "-")
    return source_file.removesuffix(".jsonl")


def safe_len(value: object) -> int:
    if isinstance(value, str):
        return len(value)
    if pd.isna(value):
        return 0
    return len(str(value))


def count_lines(value: object) -> int:
    if not isinstance(value, str) or not value.strip():
        return 0
    return len(value.splitlines())


def error_text(errors: object) -> str:
    if isinstance(errors, list):
        return "\n".join(map(str, errors))
    if pd.isna(errors):
        return ""
    return str(errors)


def classify_error(errors: object, extracted_code: object) -> str:
    text = error_text(errors).lower()
    code = extracted_code if isinstance(extracted_code, str) else ""
    if not code.strip():
        return "missing_or_empty_code"
    if not text.strip():
        return "none"
    if "not defined" in text:
        return "name_not_defined"
    if "syntax" in text or "invalid syntax" in text:
        return "syntax_error"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "importerror" in text or "no module named" in text:
        return "import_error"
    if "assert" in text or "test failed" in text:
        return "wrong_answer"
    return "other_runtime"


def expected_function_name(test_cases: object, challenge_tests: object) -> str:
    text = f"{test_cases}\n{challenge_tests}"
    match = re.search(r"assert\s+([A-Za-z_]\w*)\s*\(", text)
    return match.group(1) if match else ""


def strip_markdown_fence(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def raw_response_code_indicators(text: str) -> list[str]:
    indicators = []
    if "```" in text:
        indicators.append("fence")
    if re.search(r"^\s*def\s+\w+\s*\(", text, flags=re.MULTILINE):
        indicators.append("def_at_line_start")
    if re.search(r"\bdef\s+\w+\s*\(", text):
        indicators.append("contains_def")
    if re.search(r"\breturn\b", text):
        indicators.append("contains_return")
    if re.search(r"\bimport\s+\w+|\bfrom\s+\w+\s+import\b", text):
        indicators.append("contains_import")
    if re.search(r"\bclass\s+\w+\s*[:(]", text):
        indicators.append("contains_class")
    return indicators


def audit_empty_extractions(df: pd.DataFrame) -> pd.DataFrame:
    import ast

    rows = []
    subset = df[df["extraction_failed"].eq(1)].copy()
    for _, row in subset.iterrows():
        response = row.get("response_text") or ""
        candidate = strip_markdown_fence(response)
        indicators = raw_response_code_indicators(response)
        syntax_ok = False
        syntax_error = ""
        functions = []
        try:
            tree = ast.parse(candidate)
            syntax_ok = True
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except SyntaxError as exc:
            syntax_error = f"{exc.__class__.__name__}: {exc.msg} at line {exc.lineno}"

        expected = row.get("expected_function") or ""
        rows.append(
            {
                "model_short": row["model_short"],
                "task_id": row["task_id"],
                "problem_id": row["problem_id"],
                "template_id": row["template_id"],
                "Tone": row["Tone"],
                "Role_framing": row["Role_framing"],
                "Format": row["Format"],
                "expected_function": expected,
                "raw_has_code_indicators": bool(indicators),
                "indicators": ";".join(indicators),
                "syntax_ok": syntax_ok,
                "defined_functions": ";".join(functions),
                "defines_expected_function": expected in functions,
                "response_chars": len(response),
                "candidate_chars": len(candidate),
                "syntax_error": syntax_error,
                "response_preview": response[:240].replace("\n", "\\n"),
            }
        )
    return pd.DataFrame(rows)


def load_data() -> pd.DataFrame:
    problems = pd.read_csv(PROBLEMS_PATH)
    prompt_matrix = pd.read_csv(PROMPT_MATRIX_PATH).rename(
        columns={"ID": "template_id", "Role framing": "Role_framing"}
    )
    result_paths = sorted(RESULTS_DIR.glob("*_final.jsonl"))
    if not result_paths:
        raise FileNotFoundError(f"No *_final.jsonl files found in {RESULTS_DIR}")

    results = pd.concat([read_jsonl(path) for path in result_paths], ignore_index=True)
    parsed_ids = results["task_id"].map(parse_result_task_id)
    results["problem_id"] = parsed_ids.map(lambda pair: pair[0])
    results["template_id"] = parsed_ids.map(lambda pair: pair[1])
    results["model_short"] = [
        short_model_name(src, model)
        for src, model in zip(results["source_file"], results.get("model", pd.Series([None] * len(results))))
    ]

    problem_meta = (
        problems.rename(columns={"task_id": "problem_id"})
        .sort_values(["problem_id", "category_id"])
        .drop_duplicates("problem_id")
        [["problem_id", "prompt", "test_cases", "challenge_test_list"]]
    )

    df = (
        results.merge(prompt_matrix, on="template_id", how="left", validate="many_to_one")
        .merge(problem_meta, on="problem_id", how="left", validate="many_to_one", suffixes=("", "_problem"))
    )

    df["passed_int"] = df["passed"].astype(bool).astype(int)
    df["tests_passed"] = pd.to_numeric(df["tests_passed"], errors="coerce")
    df["tests_total"] = pd.to_numeric(df["tests_total"], errors="coerce")
    df["tests_fraction"] = np.where(df["tests_total"] > 0, df["tests_passed"] / df["tests_total"], np.nan)
    df["prompt_tokens"] = pd.to_numeric(df["prompt_tokens"], errors="coerce")
    df["completion_tokens"] = pd.to_numeric(df["completion_tokens"], errors="coerce")
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")
    df["response_chars"] = df["response_text"].map(safe_len)
    df["code_chars"] = df["extracted_code"].map(safe_len)
    df["response_lines"] = df["response_text"].map(count_lines)
    df["code_lines"] = df["extracted_code"].map(count_lines)
    df["has_extracted_code"] = (df["code_chars"] > 0).astype(int)
    df["extraction_failed"] = (df["has_extracted_code"] == 0).astype(int)
    df["extra_text_chars"] = (df["response_chars"] - df["code_chars"]).clip(lower=0)
    df["extra_text_ratio"] = np.where(df["response_chars"] > 0, df["extra_text_chars"] / df["response_chars"], np.nan)
    df["likely_code_only"] = ((df["has_extracted_code"] == 1) & (df["extra_text_ratio"] < 0.15)).astype(int)
    df["error_text"] = df["errors"].map(error_text)
    df["error_category"] = [classify_error(e, c) for e, c in zip(df["errors"], df["extracted_code"])]
    df["expected_function"] = [
        expected_function_name(t, c) for t, c in zip(df["test_cases"], df["challenge_test_list"])
    ]
    df["runtime_failure"] = df["error_category"].isin(
        ["syntax_error", "name_not_defined", "import_error", "other_runtime", "timeout", "missing_or_empty_code"]
    ).astype(int)
    df["log_completion_tokens"] = np.log1p(df["completion_tokens"])
    df["log_duration_seconds"] = np.log1p(df["duration_seconds"])

    return df


def mean_ci(series: pd.Series, z: float = 1.96) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").dropna()
    n = len(values)
    mean = values.mean() if n else np.nan
    se = values.std(ddof=1) / math.sqrt(n) if n > 1 else np.nan
    return pd.Series(
        {
            "mean": mean,
            "ci_low": mean - z * se if n > 1 else np.nan,
            "ci_high": mean + z * se if n > 1 else np.nan,
            "n": n,
        }
    )


def coef_rows(result, model_name: str, outcome: str) -> pd.DataFrame:
    rows = result.params.rename("coef").to_frame()
    rows["std_err"] = result.bse
    rows["p_value"] = result.pvalues
    rows["model_spec"] = model_name
    rows["outcome"] = outcome
    rows["term"] = rows.index
    return rows.reset_index(drop=True)


def fit_ols(df: pd.DataFrame, outcome: str, controls: list[str], spec_name: str):
    prompt_terms = "C(Tone) + C(Role_framing) + C(Format)"
    fixed_effects = "C(model_short) + C(problem_id)"
    rhs_terms = [prompt_terms, fixed_effects, *controls]
    formula = f"{outcome} ~ " + " + ".join(rhs_terms)
    model_cols = [outcome, "Tone", "Role_framing", "Format", "model_short", "problem_id", *controls]
    model_data = df[model_cols].dropna()
    result = smf.ols(formula, data=model_data).fit(cov_type="HC3")
    return result, formula


def fit_glm_binomial(df: pd.DataFrame, controls: list[str], spec_name: str):
    prompt_terms = "C(Tone) + C(Role_framing) + C(Format)"
    fixed_effects = "C(model_short) + C(problem_id)"
    rhs_terms = [prompt_terms, fixed_effects, *controls]
    formula = "passed_int ~ " + " + ".join(rhs_terms)
    model_cols = ["passed_int", "Tone", "Role_framing", "Format", "model_short", "problem_id", *controls]
    model_data = df[model_cols].dropna()
    result = smf.glm(formula=formula, data=model_data, family=__import__("statsmodels.api").api.families.Binomial()).fit(
        cov_type="HC3"
    )
    return result, formula


def main() -> None:
    df = load_data()
    df.to_csv(OUTPUT_DIR / "joined_deep_behavior_data.csv", index=False)

    empty_extraction_audit = audit_empty_extractions(df)
    empty_extraction_audit.to_csv(OUTPUT_DIR / "empty_extraction_audit.csv", index=False)

    summary_metrics = [
        "passed_int",
        "tests_fraction",
        "completion_tokens",
        "duration_seconds",
        "likely_code_only",
        "extraction_failed",
        "runtime_failure",
        "extra_text_ratio",
    ]

    tone_summary_parts = []
    for metric in summary_metrics:
        part = df.groupby("Tone")[metric].apply(mean_ci).unstack().reset_index()
        part.insert(1, "metric", metric)
        tone_summary_parts.append(part)
    tone_summary = pd.concat(tone_summary_parts, ignore_index=True)
    tone_summary.to_csv(OUTPUT_DIR / "tone_behavior_summary.csv", index=False)

    error_summary = (
        df.groupby(["Tone", "error_category"])
        .size()
        .rename("runs")
        .reset_index()
        .assign(rate=lambda x: x["runs"] / x.groupby("Tone")["runs"].transform("sum"))
        .sort_values(["Tone", "runs"], ascending=[True, False])
    )
    error_summary.to_csv(OUTPUT_DIR / "tone_error_category_summary.csv", index=False)

    control_sets = {
        "M0_prompt_only": [],
        "M1_length": ["log_completion_tokens"],
        "M2_code_only": ["likely_code_only"],
        "M3_extraction": ["extraction_failed"],
        "M4_runtime": ["log_duration_seconds"],
        "M5_all_behavior_controls": [
            "log_completion_tokens",
            "likely_code_only",
            "extraction_failed",
            "log_duration_seconds",
        ],
    }

    rows = []
    formulas = []
    for outcome in ["passed_int", "tests_fraction"]:
        for spec_name, controls in control_sets.items():
            result, formula = fit_ols(df, outcome, controls, spec_name)
            rows.append(coef_rows(result, spec_name, outcome))
            formulas.append({"outcome": outcome, "model_spec": spec_name, "formula": formula, "nobs": result.nobs, "rsquared": result.rsquared})

    ols_results = pd.concat(rows, ignore_index=True)
    ols_results.to_csv(OUTPUT_DIR / "behavior_control_ols_models.csv", index=False)
    pd.DataFrame(formulas).to_csv(OUTPUT_DIR / "behavior_control_ols_formulas.csv", index=False)

    glm_rows = []
    glm_formulas = []
    for spec_name, controls in control_sets.items():
        result, formula = fit_glm_binomial(df, controls, spec_name)
        glm_rows.append(coef_rows(result, spec_name, "passed_int_glm_binomial_logit"))
        glm_formulas.append({"outcome": "passed_int", "model_spec": spec_name, "formula": formula, "nobs": result.nobs, "aic": result.aic})
    glm_results = pd.concat(glm_rows, ignore_index=True)
    glm_results.to_csv(OUTPUT_DIR / "behavior_control_glm_logit_models.csv", index=False)
    pd.DataFrame(glm_formulas).to_csv(OUTPUT_DIR / "behavior_control_glm_formulas.csv", index=False)

    focus_terms = [
        "C(Tone)[T.neutral]",
        "C(Tone)[T.polite]",
        "log_completion_tokens",
        "likely_code_only",
        "extraction_failed",
        "log_duration_seconds",
    ]
    focus_ols = ols_results[ols_results["term"].isin(focus_terms)].copy()
    focus_ols.to_csv(OUTPUT_DIR / "focus_ols_terms.csv", index=False)
    focus_glm = glm_results[glm_results["term"].isin(focus_terms)].copy()
    focus_glm.to_csv(OUTPUT_DIR / "focus_glm_terms.csv", index=False)

    model_tone = (
        df.groupby(["model_short", "Tone"])
        .agg(
            runs=("task_id", "size"),
            pass_rate=("passed_int", "mean"),
            tests_fraction=("tests_fraction", "mean"),
            avg_completion_tokens=("completion_tokens", "mean"),
            avg_duration_seconds=("duration_seconds", "mean"),
            code_only_rate=("likely_code_only", "mean"),
            extraction_failure_rate=("extraction_failed", "mean"),
            runtime_failure_rate=("runtime_failure", "mean"),
        )
        .reset_index()
        .sort_values(["model_short", "tests_fraction"], ascending=[True, False])
    )
    model_tone.to_csv(OUTPUT_DIR / "model_by_tone_behavior_summary.csv", index=False)

    problem_difficulty = (
        df.groupby("problem_id")
        .agg(problem_mean_tests_fraction=("tests_fraction", "mean"), problem_pass_rate=("passed_int", "mean"))
        .reset_index()
    )
    problem_difficulty["difficulty_band"] = pd.qcut(
        problem_difficulty["problem_mean_tests_fraction"],
        q=3,
        labels=["hard", "medium", "easy"],
        duplicates="drop",
    )
    df = df.merge(problem_difficulty[["problem_id", "difficulty_band"]], on="problem_id", how="left")
    difficulty_tone = (
        df.groupby(["difficulty_band", "Tone"], observed=False)
        .agg(
            runs=("task_id", "size"),
            pass_rate=("passed_int", "mean"),
            tests_fraction=("tests_fraction", "mean"),
            avg_completion_tokens=("completion_tokens", "mean"),
            avg_duration_seconds=("duration_seconds", "mean"),
            code_only_rate=("likely_code_only", "mean"),
            extraction_failure_rate=("extraction_failed", "mean"),
            runtime_failure_rate=("runtime_failure", "mean"),
        )
        .reset_index()
    )
    difficulty_tone.to_csv(OUTPUT_DIR / "difficulty_by_tone_behavior_summary.csv", index=False)

    corr_cols = [
        "passed_int",
        "tests_fraction",
        "completion_tokens",
        "duration_seconds",
        "likely_code_only",
        "extraction_failed",
        "runtime_failure",
        "extra_text_ratio",
    ]
    correlations = df[corr_cols].corr(method="pearson").reset_index().rename(columns={"index": "metric"})
    correlations.to_csv(OUTPUT_DIR / "behavior_metric_correlations.csv", index=False)

    print(f"Rows analyzed: {len(df):,}")
    print(f"Outputs written to: {OUTPUT_DIR}")
    if not empty_extraction_audit.empty:
        print("\nEmpty extraction audit:")
        print(
            empty_extraction_audit[
                ["raw_has_code_indicators", "syntax_ok", "defines_expected_function"]
            ].mean().round(4).to_string()
        )
    print("\nTone summary:")
    print(tone_summary.pivot(index="Tone", columns="metric", values="mean").round(4).to_string())
    print("\nOLS focus terms:")
    print(focus_ols[["outcome", "model_spec", "term", "coef", "std_err", "p_value"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
