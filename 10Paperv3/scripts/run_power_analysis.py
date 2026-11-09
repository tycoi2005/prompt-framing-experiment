"""Design-based power analysis for the stratified prompt contrasts.

The experiment is not a simple random sample: every base task contributes 18
prompt variants under each model, so observations are clustered within 50 base
tasks per stratum. This script turns the realized design into the quantities a
reader needs to judge statistical power, without running any new LLM calls:

* ``cluster_se_pp``          task-clustered standard error of each prompt
                            contrast, read from ``clustered_lpm_prompt_effects.csv``
* ``naive_se_pp``           i.i.d. (unclustered) standard error from the same
                            linear probability model
* ``design_effect``         (cluster SE / naive SE)^2, i.e. the variance
                            inflation induced by the 18-within-task design
* ``effective_n``           n / design effect
* ``mde_80_pp`` / ``mde_90_pp``  minimum detectable effect at 80% / 90% power,
                            two-sided alpha = 0.05: (z_{0.975} + z_power) * SE
* ``achieved_power``        Phi(|beta| / SE - z_{0.975}) for the observed effect
* ``tasks_for_1pp`` / ``tasks_for_2pp``  base tasks that would be required, at
                            the same design, to detect a 1 pp / 2 pp contrast
                            at 80% power (SE scales as 1/sqrt(K))

The stratum-level ICC of Pass@1 across base tasks is reported alongside, because
it is the parameter that drives the design effect.

Outputs
-------
``analysis/manuscript_power_analysis.csv``      one row per stratum x contrast
``analysis/manuscript_power_summary.csv``       one row per stratum
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recompute_manuscript_tables import (  # noqa: E402
    OUT_DIR,
    PROMPT_TERMS,
    TERM_LABELS,
    fit_lpm,
    load_dataset,
    write_csv,
)

Z_ALPHA = 1.959963984540054  # two-sided 0.05
Z_POWER = {0.80: 0.8416212335729143, 0.90: 1.2815515655446004}
STRATA = [
    ("local", "code", "Local code"),
    ("local", "math", "Local math"),
    ("api", "code", "API Python"),
    ("api", "math", "API math"),
]
CONTRAST_TERMS = {
    "aggressive vs neutral": "tone_aggressive",
    "polite vs neutral": "tone_polite",
    "role vs none": "role_vs_no_role",
    "JSON vs plaintext": "format_json",
    "XML vs plaintext": "format_xml",
}
FE_COLS = ["modelname", "base_task"]


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def icc_oneway(values: pd.Series, clusters: pd.Series) -> tuple[float, float]:
    """One-way random-effects ICC of a binary outcome across base tasks."""

    frame = pd.DataFrame({"y": values.astype(float), "cluster": clusters})
    grouped = frame.groupby("cluster")["y"]
    k = grouped.ngroups
    n = len(frame)
    if k < 2 or n <= k:
        return float("nan"), float("nan")
    grand = frame["y"].mean()
    ss_between = float((grouped.mean() - grand).pow(2).sum() * (n / k))
    ss_within = float(grouped.apply(lambda s: ((s - s.mean()) ** 2).sum()).sum())
    ms_between = ss_between / (k - 1)
    ms_within = ss_within / (n - k)
    m = n / k
    denominator = ms_between + (m - 1) * ms_within
    icc = (ms_between - ms_within) / denominator if denominator > 0 else float("nan")
    return icc, m


def main() -> None:
    df = load_dataset()
    clustered = pd.read_csv(OUT_DIR / "clustered_lpm_prompt_effects.csv")
    rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for modeltype, task_type, label in STRATA:
        subset = df[df["modeltype"].eq(modeltype) & df["task_type"].eq(task_type)]
        naive = fit_lpm(subset, "passed_float", PROMPT_TERMS, FE_COLS)
        icc, mean_cluster_size = icc_oneway(
            subset["passed_float"], subset["base_task"]
        )
        stratum_rows = []
        for _, crow in clustered[
            clustered["modeltype"].eq(modeltype) & clustered["task_type"].eq(task_type)
        ].iterrows():
            term = CONTRAST_TERMS.get(crow["contrast"])
            if term is None:
                continue
            coef_pp = float(crow["coefficient_pp"])
            cluster_se = float(crow["cluster_se_pp"])
            naive_se = float(naive[term]["std_err_pp"])
            design_effect = (cluster_se / naive_se) ** 2 if naive_se > 0 else float("nan")
            effective_n = len(subset) / design_effect if design_effect > 0 else float("nan")
            mde_80 = (Z_ALPHA + Z_POWER[0.80]) * cluster_se
            mde_90 = (Z_ALPHA + Z_POWER[0.90]) * cluster_se
            achieved = normal_cdf(abs(coef_pp) / cluster_se - Z_ALPHA) if cluster_se > 0 else float("nan")
            row = {
                "task_group": label,
                "factor": term,
                "factor_label": TERM_LABELS[term],
                "coefficient_pp": coef_pp,
                "cluster_se_pp": cluster_se,
                "naive_se_pp": naive_se,
                "design_effect": design_effect,
                "effective_n": effective_n,
                "mde_80_pp": mde_80,
                "mde_90_pp": mde_90,
                "achieved_power": achieved,
                "tasks_for_1pp": int(math.ceil(50 * (mde_80 / 1.0) ** 2)),
                "tasks_for_2pp": int(math.ceil(50 * (mde_80 / 2.0) ** 2)),
                "n_observations": len(subset),
                "n_tasks": int(subset["base_task"].nunique()),
                "n_models": int(subset["modelname"].nunique()),
                "icc_pass_at_1": icc,
                "mean_observations_per_task": mean_cluster_size,
            }
            rows.append(row)
            stratum_rows.append(row)

        if not stratum_rows:
            continue
        mdes = [r["mde_80_pp"] for r in stratum_rows]
        summary_rows.append(
            {
                "task_group": label,
                "n_observations": stratum_rows[0]["n_observations"],
                "n_tasks": stratum_rows[0]["n_tasks"],
                "n_models": stratum_rows[0]["n_models"],
                "observations_per_task": stratum_rows[0]["mean_observations_per_task"],
                "icc_pass_at_1": icc,
                "design_effect_min": min(r["design_effect"] for r in stratum_rows),
                "design_effect_max": max(r["design_effect"] for r in stratum_rows),
                "cluster_se_min_pp": min(r["cluster_se_pp"] for r in stratum_rows),
                "cluster_se_max_pp": max(r["cluster_se_pp"] for r in stratum_rows),
                "mde_80_min_pp": min(mdes),
                "mde_80_max_pp": max(mdes),
                "mde_80_median_pp": float(np.median(mdes)),
                "mde_90_median_pp": float(np.median([r["mde_90_pp"] for r in stratum_rows])),
                "tasks_for_1pp": max(r["tasks_for_1pp"] for r in stratum_rows),
                "tasks_for_2pp": max(r["tasks_for_2pp"] for r in stratum_rows),
            }
        )

    write_csv(
        OUT_DIR / "manuscript_power_analysis.csv",
        rows,
        [
            "task_group",
            "factor",
            "factor_label",
            "coefficient_pp",
            "cluster_se_pp",
            "naive_se_pp",
            "design_effect",
            "effective_n",
            "mde_80_pp",
            "mde_90_pp",
            "achieved_power",
            "tasks_for_1pp",
            "tasks_for_2pp",
            "n_observations",
            "n_tasks",
            "n_models",
            "icc_pass_at_1",
            "mean_observations_per_task",
        ],
    )
    write_csv(
        OUT_DIR / "manuscript_power_summary.csv",
        summary_rows,
        [
            "task_group",
            "n_observations",
            "n_tasks",
            "n_models",
            "observations_per_task",
            "icc_pass_at_1",
            "design_effect_min",
            "design_effect_max",
            "cluster_se_min_pp",
            "cluster_se_max_pp",
            "mde_80_min_pp",
            "mde_80_max_pp",
            "mde_80_median_pp",
            "mde_90_median_pp",
            "tasks_for_1pp",
            "tasks_for_2pp",
        ],
    )

    for row in summary_rows:
        print(
            f"{row['task_group']:11s} ICC={row['icc_pass_at_1']:.3f} "
            f"DE={row['design_effect_min']:.1f}-{row['design_effect_max']:.1f} "
            f"SE={row['cluster_se_min_pp']:.2f}-{row['cluster_se_max_pp']:.2f} pp "
            f"MDE80={row['mde_80_min_pp']:.2f}-{row['mde_80_max_pp']:.2f} pp "
            f"K(1pp)={row['tasks_for_1pp']} K(2pp)={row['tasks_for_2pp']}"
        )


if __name__ == "__main__":
    main()
