from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from collections import defaultdict

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "02ScalingPhrase" / "results_analysis" / "prompt_framing_experiment_results.jsonl"
CODE_TEMPLATE = ROOT.parent / "02ScalingPhrase" / "results_analysis" / "prompt_templates" / "prompt_matrix_prompt_template.09.csv"
MATH_TEMPLATE = ROOT.parent / "02ScalingPhrase" / "results_analysis" / "prompt_templates" / "prompt_matrix_prompt_template.09.math.csv"
OUT_DIR = ROOT / "analysis"
OUT_CSV = OUT_DIR / "clustered_lpm_prompt_effects.csv"
OUT_MD = ROOT / "clustered_lpm_audit.md"


TERM_LABELS = {
    "tone_aggressive": ("tone", "aggressive vs neutral"),
    "tone_polite": ("tone", "polite vs neutral"),
    "role_role": ("role", "role vs none"),
    "format_json": ("format", "JSON vs plaintext"),
    "format_xml": ("format", "XML vs plaintext"),
}


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


def load_dataset() -> list[dict[str, object]]:
    metadata = load_prompt_metadata()
    rows: list[dict[str, object]] = []

    with SOURCE.open() as handle:
        for line in handle:
            row = json.loads(line)
            task_type = row["task_type"]
            variant, base_task = parse_variant_and_base(row)
            prompt_metadata = metadata[(task_type, variant)]

            rows.append(
                {
                    "passed": int(bool(row["passed"])),
                    "modeltype": row["modeltype"],
                    "task_type": task_type,
                    "modelname": row["modelname"],
                    "base_task": base_task,
                    **prompt_metadata,
                }
            )

    return rows


def build_design_matrix(group: list[dict[str, object]]) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    models = sorted({str(row["modelname"]) for row in group})
    model_columns = models[1:]
    column_names = [
        "intercept",
        "tone_aggressive",
        "tone_polite",
        "role_role",
        "format_json",
        "format_xml",
        *[f"model_{model}" for model in model_columns],
    ]

    x_rows: list[list[float]] = []
    y_values: list[float] = []
    clusters: list[str] = []

    for row in group:
        modelname = str(row["modelname"])
        x_rows.append(
            [
                1.0,
                float(row["tone"] == "aggressive"),
                float(row["tone"] == "polite"),
                float(row["role_binary"] == "role"),
                float(row["format"] == "json"),
                float(row["format"] == "xml"),
                *[float(modelname == model) for model in model_columns],
            ]
        )
        y_values.append(float(row["passed"]))
        clusters.append(str(row["base_task"]))

    return (
        np.asarray(x_rows, dtype=float),
        np.asarray(y_values, dtype=float),
        column_names,
        clusters,
    )


def fit_clustered_ols(
    group: list[dict[str, object]],
) -> tuple[dict[str, float], dict[str, float], dict[str, float], int, int]:
    x_matrix, y_values, column_names, clusters = build_design_matrix(group)
    beta = np.linalg.lstsq(x_matrix, y_values, rcond=None)[0]
    residuals = y_values - x_matrix @ beta

    xtx_inv = np.linalg.inv(x_matrix.T @ x_matrix)
    meat = np.zeros((x_matrix.shape[1], x_matrix.shape[1]))
    for cluster in sorted(set(clusters)):
        indices = [index for index, value in enumerate(clusters) if value == cluster]
        x_group = x_matrix[indices]
        u_group = residuals[indices][:, None]
        score = x_group.T @ u_group
        meat += score @ score.T

    n_observations, n_parameters = x_matrix.shape
    n_clusters = len(set(clusters))
    finite_sample_correction = (n_clusters / (n_clusters - 1)) * (
        (n_observations - 1) / (n_observations - n_parameters)
    )
    covariance = xtx_inv @ meat @ xtx_inv * finite_sample_correction
    standard_errors = np.sqrt(np.diag(covariance))

    coefficients = dict(zip(column_names, beta))
    cluster_ses = dict(zip(column_names, standard_errors))
    p_values = {
        name: math.erfc(abs(coefficients[name] / cluster_ses[name]) / math.sqrt(2))
        for name in column_names
    }
    return coefficients, cluster_ses, p_values, n_observations, n_clusters


def fit_models(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output_rows: list[dict[str, object]] = []
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    for row in rows:
        groups[(str(row["modeltype"]), str(row["task_type"]))].append(row)

    for (modeltype, task_type), group in sorted(groups.items()):
        coefficients, cluster_ses, p_values, observations, clusters = fit_clustered_ols(group)

        for term_name, (factor, contrast) in TERM_LABELS.items():
            output_rows.append(
                {
                    "modeltype": modeltype,
                    "task_type": task_type,
                    "factor": factor,
                    "contrast": contrast,
                    "coefficient_pp": coefficients[term_name] * 100,
                    "cluster_se_pp": cluster_ses[term_name] * 100,
                    "cluster_p": p_values[term_name],
                    "observations": observations,
                    "clusters": clusters,
                    "model_fixed_effects": True,
                }
            )

    return output_rows


def format_p(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def write_outputs(rows: list[dict[str, object]]) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    fieldnames = [
        "modeltype",
        "task_type",
        "factor",
        "contrast",
        "coefficient_pp",
        "cluster_se_pp",
        "cluster_p",
        "observations",
        "clusters",
        "model_fixed_effects",
    ]
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "coefficient_pp": f"{row['coefficient_pp']:.6f}",
                    "cluster_se_pp": f"{row['cluster_se_pp']:.6f}",
                    "cluster_p": f"{row['cluster_p']:.12g}",
                }
            )

    selected = [
        row
        for row in rows
        if row["cluster_p"] < 0.05
        or (row["modeltype"], row["task_type"], row["contrast"]) == ("api", "code", "JSON vs plaintext")
    ]

    lines = [
        "# Clustered Linear-Probability Robustness Audit",
        "",
        f"Source data: `{SOURCE.relative_to(ROOT.parent)}`.",
        "",
        "Each model is an OLS linear-probability model for pass/fail outcome with prompt factors and model fixed effects. Standard errors are clustered by base task. Models are fitted separately for local code, local math, API Python, and API math.",
        "",
        "## Selected Results",
        "",
        "| Group | Contrast | Coeff. | Cluster SE | p |",
        "|---|---|---:|---:|---:|",
    ]
    for row in selected:
        group_labels = {
            ("api", "code"): "API Python",
            ("api", "math"): "API math",
            ("local", "code"): "Local code",
            ("local", "math"): "Local math",
        }
        group = group_labels.get((row["modeltype"], row["task_type"]), f"{row['modeltype']} {row['task_type']}")
        lines.append(
            "| {group} | {contrast} | {coef:+.2f} pp | {se:.2f} pp | {p} |".format(
                group=group,
                contrast=row["contrast"],
                coef=row["coefficient_pp"],
                se=row["cluster_se_pp"],
                p=format_p(row["cluster_p"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The clustered analysis preserves the main direction of the headline pass-rate effects while changing some uncertainty estimates. API Python XML remains significant, while API Python JSON becomes marginal. Local math JSON, XML, role framing, and polite tone are significant with task-clustered standard errors. A small local-code role penalty also appears, but its magnitude is about one percentage point and should be interpreted cautiously because the paper treats clustered LPMs as robustness checks rather than final causal estimates.",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    dataset = load_dataset()
    rows = fit_models(dataset)
    write_outputs(rows)


if __name__ == "__main__":
    main()
