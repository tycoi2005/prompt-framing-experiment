"""Single-run noise accounting for the R1-3 / R2-Maj-14 comments.

The study collects one execution per prompt x task x model cell. This script
does not create new runs; it computes what the existing one-run design can and
cannot say about run-to-run variability, using the recorded binary outcomes.

Two quantities are reported for every stratum and every model-task cell:

* ``bernoulli_se_pp`` -- the standard error of a prompt contrast that would
  arise *purely* from single-run Bernoulli sampling with independent runs
  (``sqrt(p0(1-p0)/n0 + p1(1-p1)/n1)``, in percentage points). This is the
  noise floor implied by one shot per cell.
* the realized task-clustered standard error from the linear probability model,
  for comparison. A clustered SE at or below the Bernoulli floor means the
  reported uncertainty is already dominated by--and therefore already
  contains--single-run sampling noise, with task and model blocking removing
  the rest.

The script also reports the contrast that would remain detectable if the
within-cell variance were twice the Bernoulli value (a deliberately
conservative allowance for model-side non-determinism that the one-run design
cannot separately estimate): ``mde_80_if_double_pp = sqrt(2) * mde_80_pp``.

Outputs
-------
``analysis/manuscript_single_run_noise.csv``        one row per stratum x contrast
``analysis/manuscript_single_run_noise_models.csv`` one row per model-task cell
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recompute_manuscript_tables import (  # noqa: E402
    OUT_DIR,
    PROMPT_TERMS,
    TERM_LABELS,
    load_dataset,
    write_csv,
)

Z80 = 1.959963984540054 + 0.8416212335729143
STRATA = [
    ("local", "code", "Local code"),
    ("local", "math", "Local math"),
    ("api", "code", "API Python"),
    ("api", "math", "API math"),
]
SPECS = [
    ("tone", "neutral", "aggressive", "tone_aggressive"),
    ("tone", "neutral", "polite", "tone_polite"),
    ("role_binary", "no role", "role", "role_vs_no_role"),
    ("format", "plaintext", "json", "format_json"),
    ("format", "plaintext", "xml", "format_xml"),
]


def bernoulli_se(subset: pd.DataFrame, factor: str, base: str, level: str) -> tuple[float, int, int]:
    base_rows = subset[subset[factor].eq(base)]
    level_rows = subset[subset[factor].eq(level)]
    p0 = float(base_rows["passed_float"].mean())
    p1 = float(level_rows["passed_float"].mean())
    n0, n1 = len(base_rows), len(level_rows)
    var = p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1
    return 100 * math.sqrt(var), n0, n1


def main() -> None:
    df = load_dataset()
    clustered = pd.read_csv(OUT_DIR / "clustered_lpm_prompt_effects.csv")
    power = pd.read_csv(OUT_DIR / "manuscript_power_analysis.csv")

    rows: list[dict[str, object]] = []
    model_rows: list[dict[str, object]] = []

    for modeltype, task_type, label in STRATA:
        subset = df[df["modeltype"].eq(modeltype) & df["task_type"].eq(task_type)]
        stratum_power = power[power["task_group"].eq(label)].set_index("factor")
        stratum_cluster = clustered[
            clustered["modeltype"].eq(modeltype) & clustered["task_type"].eq(task_type)
        ]
        for factor, base, level, term in SPECS:
            se_b, n0, n1 = bernoulli_se(subset, factor, base, level)
            match = stratum_cluster[
                stratum_cluster["contrast"].eq(
                    {
                        "tone_aggressive": "aggressive vs neutral",
                        "tone_polite": "polite vs neutral",
                        "role_vs_no_role": "role vs none",
                        "format_json": "JSON vs plaintext",
                        "format_xml": "XML vs plaintext",
                    }[term]
                )
            ]
            cluster_se = float(match["cluster_se_pp"].iloc[0]) if len(match) else float("nan")
            mde80 = float(stratum_power.loc[term, "mde_80_pp"])
            row = {
                "task_group": label,
                "factor": term,
                "factor_label": TERM_LABELS[term],
                "baseline_rate": float(subset["passed_float"].mean()),
                "n_reference": n0,
                "n_level": n1,
                "bernoulli_se_pp": se_b,
                "cluster_se_pp": cluster_se,
                "cluster_to_bernoulli_ratio": cluster_se / se_b if se_b > 0 else float("nan"),
                "mde_80_pp": mde80,
                "mde_80_if_double_pp": math.sqrt(2) * mde80,
            }
            rows.append(row)

        # Per-model cells: 50 tasks x 18 variants per model-task.
        for modelname, cell in subset.groupby("modelname"):
            se_model = []
            for factor, base, level, _ in SPECS:
                se_b, _, _ = bernoulli_se(cell, factor, base, level)
                se_model.append(se_b)
            model_rows.append(
                {
                    "task_group": label,
                    "modelname": modelname,
                    "n_observations": len(cell),
                    "pass_rate": float(cell["passed_float"].mean()),
                    "bernoulli_se_min_pp": min(se_model),
                    "bernoulli_se_max_pp": max(se_model),
                    "mde_80_min_pp": Z80 * min(se_model),
                    "mde_80_max_pp": Z80 * max(se_model),
                }
            )

    write_csv(
        OUT_DIR / "manuscript_single_run_noise.csv",
        rows,
        [
            "task_group",
            "factor",
            "factor_label",
            "baseline_rate",
            "n_reference",
            "n_level",
            "bernoulli_se_pp",
            "cluster_se_pp",
            "cluster_to_bernoulli_ratio",
            "mde_80_pp",
            "mde_80_if_double_pp",
        ],
    )
    write_csv(
        OUT_DIR / "manuscript_single_run_noise_models.csv",
        model_rows,
        [
            "task_group",
            "modelname",
            "n_observations",
            "pass_rate",
            "bernoulli_se_min_pp",
            "bernoulli_se_max_pp",
            "mde_80_min_pp",
            "mde_80_max_pp",
        ],
    )

    frame = pd.DataFrame(rows)
    for label, group in frame.groupby("task_group", sort=False):
        print(
            f"{label:11s} Bernoulli={group['bernoulli_se_pp'].min():.2f}-"
            f"{group['bernoulli_se_pp'].max():.2f} pp  "
            f"cluster={group['cluster_se_pp'].min():.2f}-{group['cluster_se_pp'].max():.2f} pp  "
            f"MDE80={group['mde_80_pp'].min():.2f}-{group['mde_80_pp'].max():.2f} pp  "
            f"if doubled={group['mde_80_if_double_pp'].min():.2f}-"
            f"{group['mde_80_if_double_pp'].max():.2f} pp"
        )
    models = pd.DataFrame(model_rows)
    print(
        f"per-model MDE80 range: {models['mde_80_min_pp'].min():.1f}-"
        f"{models['mde_80_max_pp'].max():.1f} pp"
    )


if __name__ == "__main__":
    main()
