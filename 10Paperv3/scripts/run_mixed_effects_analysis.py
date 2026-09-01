"""Mixed-effects analysis for the prompt-framing experiment.

Feedback point 1: the repeated-measures structure (same base tasks evaluated
across 18 prompt variants and multiple models) is modelled explicitly.

Main inferential model for pass/fail:
    logistic mixed-effects model (BinomialBayesMixedGLM, variational Bayes)
    fixed effects: tone, role, format factors + model fixed effects
    random intercept: base task
    fitted separately per stratum (local code, local math, API code, API math)

Reported per term:
    - log-odds coefficient, posterior SD, z, p
    - odds ratio with 95% interval
    - average marginal effect (AME) in percentage points with 95% interval,
      computed over the observed covariate distribution at the mean random
      effect (random intercept = 0), intervals from posterior draws

Behavioral outcomes:
    - log completion tokens, log duration: linear mixed models (same structure)
    - result-only compliance (binary): logistic mixed model

Also produces:
    - dominant-model sensitivity (feedback point 3): all prompt effects
      re-estimated with and without the dominant model per stratum
      (Nemotron 3 Nano for local, DeepSeek V4 Flash for API), on both the
      LPM percentage-point scale and the mixed-model scale
    - Nemotron local-math task-level solve summary (feedback point 6)
"""
from __future__ import annotations

import csv
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.special import expit
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

from recompute_manuscript_tables import (
    MODEL_LABELS,
    PROMPT_TERMS,
    TERM_LABELS,
    load_dataset,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis"
OUT_PASS = OUT_DIR / "mixed_effects_pass.csv"
OUT_BEHAVIOR = OUT_DIR / "mixed_effects_behavior.csv"
OUT_DOMINANT = OUT_DIR / "dominant_model_sensitivity.csv"
OUT_NEMOTRON = OUT_DIR / "nemotron_task_solve_summary.csv"
OUT_AUDIT = ROOT / "mixed_effects_audit.md"

FE_FORMULA = (
    "passed ~ tone_aggressive + tone_polite + role_vs_no_role "
    "+ format_json + format_xml + C(modelname)"
)
VC_FORMULA = {"base_task": "0 + C(base_task)"}
N_DRAWS = 4000
# Fixed base seed: every AME computation seeds its own generator from this
# value plus the term index, so the same (stratum, term) contrast always gets
# identical draws no matter when it is computed (pass table vs dominant-model
# sensitivity table).
BASE_SEED = 42

STRATUM_LABELS = {
    ("api", "code"): "API Python",
    ("api", "math"): "API math",
    ("local", "code"): "Local code",
    ("local", "math"): "Local math",
}
DOMINANT_MODELS = {"local": "nemotron-3-nano-4b", "api": "deepseek-v4-flash"}


def norm_pvalue(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2)) if np.isfinite(z) else float("nan")


def fit_logit_mixed(df: pd.DataFrame) -> tuple[BinomialBayesMixedGLM, object]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = BinomialBayesMixedGLM.from_formula(FE_FORMULA, VC_FORMULA, df)
        result = model.fit_vb(verbose=False)
    return model, result


def fe_covariance(result: object, n_fe: int) -> np.ndarray:
    try:
        cov = np.asarray(result.cov_params(), dtype=float)[:n_fe, :n_fe]
        if np.all(np.diag(cov) > 0):
            return cov
    except Exception:
        pass
    return np.diag(np.asarray(result.fe_sd, dtype=float) ** 2)


def ame_for_term(
    model: BinomialBayesMixedGLM, result: object, term: str
) -> tuple[float, float, float]:
    """Average marginal effect of switching `term` 0 -> 1 (probability scale).

    Averaged over the observed covariate distribution and over the estimated
    base-task random-intercept distribution N(0, exp(vcp_mean)^2); intervals
    from posterior draws of the fixed effects.
    """
    exog_names = list(model.data.param_names)
    x = np.asarray(model.exog, dtype=float)
    col = exog_names.index(term)
    x1, x0 = x.copy(), x.copy()
    x1[:, col] = 1.0
    x0[:, col] = 0.0

    fe_mean = np.asarray(result.fe_mean, dtype=float)
    cov = fe_covariance(result, len(fe_mean))
    rng = np.random.default_rng(BASE_SEED + PROMPT_TERMS.index(term))
    draws = rng.multivariate_normal(fe_mean, cov, size=N_DRAWS)
    re_sd = float(np.exp(np.atleast_1d(result.vcp_mean)[0]))
    u = rng.normal(0.0, re_sd, size=(N_DRAWS, x.shape[0]))
    ames = (expit(draws @ x1.T + u) - expit(draws @ x0.T + u)).mean(axis=1)
    return (
        float(ames.mean() * 100),
        float(np.percentile(ames, 2.5) * 100),
        float(np.percentile(ames, 97.5) * 100),
    )


def logit_mixed_rows(
    df: pd.DataFrame,
    stratum: str,
    fit: tuple[BinomialBayesMixedGLM, object] | None = None,
) -> list[dict[str, object]]:
    model, result = fit if fit is not None else fit_logit_mixed(df)
    exog_names = list(model.data.param_names)
    fe_mean = np.asarray(result.fe_mean, dtype=float)
    fe_sd = np.asarray(result.fe_sd, dtype=float)

    rows = []
    for term in PROMPT_TERMS:
        col = exog_names.index(term)
        beta, sd = fe_mean[col], fe_sd[col]
        z = beta / sd if sd > 0 else float("nan")
        ame, ame_lo, ame_hi = ame_for_term(model, result, term)
        rows.append(
            {
                "stratum": stratum,
                "factor": term,
                "contrast": TERM_LABELS[term],
                "log_odds": beta,
                "posterior_sd": sd,
                "z": z,
                "p_value": norm_pvalue(z),
                "odds_ratio": math.exp(beta),
                "or_lo": math.exp(beta - 1.96 * sd),
                "or_hi": math.exp(beta + 1.96 * sd),
                "ame_pp": ame,
                "ame_lo_pp": ame_lo,
                "ame_hi_pp": ame_hi,
                "observations": int(len(df)),
                "n_base_tasks": int(df["base_task"].nunique()),
                "n_models": int(df["modelname"].nunique()),
            }
        )
    return rows


def linear_mixed_rows(df: pd.DataFrame, stratum: str, outcome: str) -> list[dict[str, object]]:
    formula = (
        f"{outcome} ~ tone_aggressive + tone_polite + role_vs_no_role "
        "+ format_json + format_xml + C(modelname)"
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = smf.mixedlm(formula, df, groups=df["base_task"]).fit(reml=False)
    scale = 100 if outcome.startswith("log") else 1
    unit = "%" if outcome.startswith("log") else "pp"
    return [
        {
            "stratum": stratum,
            "outcome": outcome,
            "factor": term,
            "contrast": TERM_LABELS[term],
            "coef": float(fit.params[term]),
            "effect_approx": float(fit.params[term] * scale),
            "unit": unit,
            "std_err": float(fit.bse[term]),
            "p_value": float(fit.pvalues[term]),
            "observations": int(fit.nobs),
            "n_base_tasks": int(df["base_task"].nunique()),
        }
        for term in PROMPT_TERMS
    ]


def compliance_mixed_rows(df: pd.DataFrame, stratum: str) -> list[dict[str, object]]:
    work = df.drop(columns=["passed"]).rename(columns={"result_only": "passed"})
    if work["passed"].nunique() < 2:
        return [
            {
                "stratum": stratum,
                "outcome": "result_only",
                "factor": term,
                "contrast": TERM_LABELS[term],
                "coef": float("nan"),
                "effect_approx": float("nan"),
                "unit": "pp (AME)",
                "std_err": float("nan"),
                "p_value": float("nan"),
                "observations": int(len(work)),
                "n_base_tasks": int(work["base_task"].nunique()),
                "note": "outcome constant in stratum; mixed model not estimable",
            }
            for term in PROMPT_TERMS
        ]
    model, result = fit_logit_mixed(work)
    exog_names = list(model.data.param_names)
    fe_mean = np.asarray(result.fe_mean, dtype=float)
    fe_sd = np.asarray(result.fe_sd, dtype=float)
    rows = []
    for term in PROMPT_TERMS:
        col = exog_names.index(term)
        beta, sd = fe_mean[col], fe_sd[col]
        z = beta / sd if sd > 0 else float("nan")
        ame, ame_lo, ame_hi = ame_for_term(model, result, term)
        rows.append(
            {
                "stratum": stratum,
                "outcome": "result_only",
                "factor": term,
                "contrast": TERM_LABELS[term],
                "coef": beta,
                "effect_approx": ame,
                "unit": "pp (AME)",
                "std_err": sd,
                "p_value": norm_pvalue(z),
                "observations": int(len(df)),
                "n_base_tasks": int(work["base_task"].nunique()),
            }
        )
    return rows


def lpm_cluster_rows(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Clustered-SE LPM per term, reused for the dominant-model sensitivity table."""
    formula = (
        "passed ~ tone_aggressive + tone_polite + role_vs_no_role "
        "+ format_json + format_xml + C(modelname)"
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = smf.ols(formula, df).fit(
            cov_type="cluster", cov_kwds={"groups": df["base_task"]}
        )
    return {
        term: {
            "lpm_pp": float(fit.params[term] * 100),
            "lpm_se_pp": float(fit.bse[term] * 100),
            "lpm_p": float(fit.pvalues[term]),
        }
        for term in PROMPT_TERMS
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def dominant_model_sensitivity(
    df: pd.DataFrame,
    fits: dict[str, tuple[BinomialBayesMixedGLM, object]] | None = None,
) -> list[dict[str, object]]:
    rows = []
    for (modeltype, task_type), group in df.groupby(["modeltype", "task_type"]):
        stratum = STRATUM_LABELS[(modeltype, task_type)]
        dominant = DOMINANT_MODELS[modeltype]
        panels = {"full panel": group, f"without {MODEL_LABELS[dominant]}": group[group["modelname"] != dominant]}
        for panel_name, panel_df in panels.items():
            lpm = lpm_cluster_rows(panel_df)
            # Reuse the full-panel fit from the main pass table so both tables
            # report identical estimates for the same model; only the
            # leave-one-out panels are fitted fresh.
            fit = fits.get(stratum) if (fits and panel_name == "full panel") else None
            mixed = {row["factor"]: row for row in logit_mixed_rows(panel_df, stratum, fit=fit)}
            for term in PROMPT_TERMS:
                rows.append(
                    {
                        "stratum": stratum,
                        "panel": panel_name,
                        "factor": term,
                        "contrast": TERM_LABELS[term],
                        **lpm[term],
                        "mixed_ame_pp": mixed[term]["ame_pp"],
                        "mixed_ame_lo_pp": mixed[term]["ame_lo_pp"],
                        "mixed_ame_hi_pp": mixed[term]["ame_hi_pp"],
                        "mixed_or": mixed[term]["odds_ratio"],
                        "mixed_p": mixed[term]["p_value"],
                        "n_models": int(panel_df["modelname"].nunique()),
                        "observations": int(len(panel_df)),
                    }
                )
    return rows


def nemotron_task_summary(df: pd.DataFrame) -> list[dict[str, object]]:
    subset = df[
        (df["modeltype"] == "local")
        & (df["task_type"] == "math")
        & (df["modelname"] == "nemotron-3-nano-4b")
    ]
    per_task = subset.groupby("base_task")["passed"].agg(["sum", "count"]).reset_index()
    per_task.columns = ["base_task", "variants_passed", "variants_total"]
    per_task["solve_category"] = pd.cut(
        per_task["variants_passed"],
        bins=[-1, 0, 17, 18],
        labels=["solved under no condition", "solved under some conditions", "solved under all 18 conditions"],
    )
    rows = per_task.to_dict("records")
    summary = per_task["solve_category"].value_counts().to_dict()
    rows.append(
        {
            "base_task": "SUMMARY",
            "variants_passed": "",
            "variants_total": "",
            "solve_category": "; ".join(f"{k}: {v}" for k, v in summary.items()),
        }
    )
    return rows, summary


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = load_dataset()
    df["passed"] = df["passed"].astype(int)
    df["result_only"] = df["result_only"].astype(int)
    df["stratum"] = df.apply(
        lambda r: STRATUM_LABELS[(r["modeltype"], r["task_type"])], axis=1
    )

    pass_rows, behavior_rows = [], []
    fits: dict[str, tuple[BinomialBayesMixedGLM, object]] = {}
    for stratum, group in df.groupby("stratum"):
        fits[stratum] = fit_logit_mixed(group)
        pass_rows.extend(logit_mixed_rows(group, stratum, fit=fits[stratum]))
        for outcome in ("log_completion_tokens", "log_duration"):
            behavior_rows.extend(linear_mixed_rows(group, stratum, outcome))
        behavior_rows.extend(compliance_mixed_rows(group, stratum))
    write_csv(OUT_PASS, pass_rows)
    write_csv(OUT_BEHAVIOR, behavior_rows)

    dominant_rows = dominant_model_sensitivity(df, fits)
    write_csv(OUT_DOMINANT, dominant_rows)

    nemotron_rows, nemotron_summary = nemotron_task_summary(df)
    write_csv(OUT_NEMOTRON, nemotron_rows)

    write_audit(pass_rows, behavior_rows, dominant_rows, nemotron_summary)


def write_audit(pass_rows, behavior_rows, dominant_rows, nemotron_summary) -> None:
    lines = [
        "# Mixed-Effects Analysis Audit",
        "",
        "Main inferential model: logistic mixed-effects model for pass/fail with",
        "tone/role/format fixed effects, model fixed effects, and a random intercept",
        "per base task with one shared variance (BinomialBayesMixedGLM, variational",
        "Bayes), fitted per stratum. AME = average marginal effect in percentage",
        "points, averaged over the observed covariates and the estimated task",
        "random-intercept distribution; intervals from posterior draws. LPM",
        "contrasts remain as interpretability layer.",
        "",
        "## Pass/fail: logistic mixed-effects results",
        "",
        "| Stratum | Contrast | OR [95% int] | AME pp [95% int] | p |",
        "|---|---|---:|---:|---:|",
    ]
    for row in pass_rows:
        lines.append(
            "| {s} | {c} | {or_:.2f} [{lo:.2f}, {hi:.2f}] | {ame:+.1f} [{alo:+.1f}, {ahi:+.1f}] | {p} |".format(
                s=row["stratum"],
                c=row["contrast"],
                or_=row["odds_ratio"],
                lo=row["or_lo"],
                hi=row["or_hi"],
                ame=row["ame_pp"],
                alo=row["ame_lo_pp"],
                ahi=row["ame_hi_pp"],
                p="<0.001" if row["p_value"] < 0.001 else f"{row['p_value']:.3f}",
            )
        )

    lines += [
        "",
        "## Behavioral outcomes: mixed models",
        "",
        "| Stratum | Outcome | Contrast | Effect | p |",
        "|---|---|---|---:|---:|",
    ]
    for row in behavior_rows:
        lines.append(
            "| {s} | {o} | {c} | {e:+.2f} {u} | {p} |".format(
                s=row["stratum"],
                o=row["outcome"],
                c=row["contrast"],
                e=row["effect_approx"],
                u=row["unit"],
                p="<0.001" if row["p_value"] < 0.001 else f"{row['p_value']:.3f}",
            )
        )

    lines += [
        "",
        "## Dominant-model sensitivity (prompt effects, full panel vs leave-one-out)",
        "",
        "| Stratum | Contrast | Panel | LPM pp | Mixed AME pp | Mixed OR |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in dominant_rows:
        lines.append(
            "| {s} | {c} | {p} | {lpm:+.1f} | {ame:+.1f} | {or_:.2f} |".format(
                s=row["stratum"],
                c=row["contrast"],
                p=row["panel"],
                lpm=row["lpm_pp"],
                ame=row["mixed_ame_pp"],
                or_=row["mixed_or"],
            )
        )

    lines += [
        "",
        "## Nemotron 3 Nano local math: task-level solve summary (50 tasks x 18 variants)",
        "",
    ]
    for key, value in nemotron_summary.items():
        lines.append(f"- {key}: {value}")

    OUT_AUDIT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
