from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "02ScalingPhrase" / "localmodel" / "results" / "analysis" / "prompt_factor_contrasts.csv"
OUT_DIR = ROOT / "analysis"
OUT_CSV = OUT_DIR / "local_model_specific_bh.csv"
OUT_MD = ROOT / "multiple_comparison_audit.md"


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = sorted(range(count), key=p_values.__getitem__)
    adjusted = [1.0] * count
    running_min = 1.0

    for rank, index in reversed(list(enumerate(order, start=1))):
        running_min = min(running_min, p_values[index] * count / rank)
        adjusted[index] = min(1.0, running_min)

    return adjusted


def load_model_specific_rows() -> list[dict[str, str]]:
    with SOURCE.open(newline="") as handle:
        rows = [
            row
            for row in csv.DictReader(handle)
            if row["model_slug"]
        ]

    for row in rows:
        row["p_value"] = f"{float(row['z_test_p_value']):.12g}"
        row["delta_pass_rate_pp"] = f"{float(row['delta_pass_rate_pp']):.3f}"

    return rows


def add_adjusted_values(rows: list[dict[str, str]], family_name: str, family_rows: list[dict[str, str]]) -> None:
    q_values = benjamini_hochberg([float(row["z_test_p_value"]) for row in family_rows])
    key = f"bh_q_{family_name}"
    sig_key = f"bh_significant_{family_name}"

    for row in rows:
        row[key] = ""
        row[sig_key] = ""

    for row, q_value in zip(family_rows, q_values):
        row[key] = f"{q_value:.12g}"
        row[sig_key] = str(q_value <= 0.05)


def summarize(rows: list[dict[str, str]], q_key: str, family_label: str) -> dict[str, str]:
    family_rows = [row for row in rows if row[q_key]]
    uncorrected = sum(float(row["z_test_p_value"]) < 0.05 for row in family_rows)
    corrected = [row for row in family_rows if float(row[q_key]) <= 0.05]

    return {
        "family": family_label,
        "contrasts": str(len(family_rows)),
        "uncorrected_significant": str(uncorrected),
        "bh_significant": str(len(corrected)),
        "survivors": corrected,
    }


def markdown_table(rows: list[dict[str, str]], q_key: str) -> str:
    if not rows:
        return "No contrasts remain significant after correction.\n"

    lines = [
        "| Kind | Model | Factor | Level | Diff | p | BH q |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {kind} | {model_slug} | {factor} | {level} | {delta_pass_rate_pp} pp | {p_value} | {q} |".format(
                kind=row["kind"],
                model_slug=row["model_slug"],
                factor=row["factor"],
                level=row["level"],
                delta_pass_rate_pp=row["delta_pass_rate_pp"],
                p_value=row["p_value"],
                q=row[q_key],
            )
        )
    return "\n".join(lines) + "\n"


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    fieldnames = [
        "kind",
        "model_slug",
        "factor",
        "baseline",
        "level",
        "delta_pass_rate_pp",
        "p_value",
        "bh_q_all",
        "bh_significant_all",
        "bh_q_code",
        "bh_significant_code",
        "bh_q_math",
        "bh_significant_math",
    ]
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})

    all_summary = summarize(rows, "bh_q_all", "All local model-specific baseline contrasts")
    code_summary = summarize(rows, "bh_q_code", "Local code baseline contrasts")
    math_summary = summarize(rows, "bh_q_math", "Local math baseline contrasts")

    all_survivors = sorted(
        all_summary["survivors"],
        key=lambda row: float(row["bh_q_all"]),
    )
    math_survivors = sorted(
        math_summary["survivors"],
        key=lambda row: float(row["bh_q_math"]),
    )

    body = f"""# Multiple-Comparison Audit

This audit applies Benjamini-Hochberg false-discovery-rate correction to the local model-specific baseline contrasts from `{SOURCE.relative_to(ROOT.parent)}`. The source table compares prompt levels against the experiment baselines: neutral tone, no role, and plaintext format.

## Families

| Family | Contrasts | Uncorrected p < 0.05 | BH q <= 0.05 |
|---|---:|---:|---:|
| {all_summary['family']} | {all_summary['contrasts']} | {all_summary['uncorrected_significant']} | {all_summary['bh_significant']} |
| {code_summary['family']} | {code_summary['contrasts']} | {code_summary['uncorrected_significant']} | {code_summary['bh_significant']} |
| {math_summary['family']} | {math_summary['contrasts']} | {math_summary['uncorrected_significant']} | {math_summary['bh_significant']} |

## Significant After BH Across All 60 Local Contrasts

{markdown_table(all_survivors, 'bh_q_all')}
## Significant After BH Within The Local Math Family

{markdown_table(math_survivors, 'bh_q_math')}
## Interpretation

The correction supports the manuscript's cautious interpretation. Local code has no model-specific baseline contrast that remains significant after task-kind-level BH correction. Local math retains the strongest heterogeneous effects: Llama 3.1 loses performance under JSON, Qwen 2.5 gains from role framing, and DeepSeek Coder loses performance under XML when correction is applied within the math family. If all local model-specific baseline contrasts are treated as one family, only the Llama JSON and Qwen role effects remain significant.
"""
    OUT_MD.write_text(body)


def main() -> None:
    rows = load_model_specific_rows()
    add_adjusted_values(rows, "all", rows)
    add_adjusted_values(rows, "code", [row for row in rows if row["kind"] == "code"])
    add_adjusted_values(rows, "math", [row for row in rows if row["kind"] == "math"])
    write_outputs(rows)


if __name__ == "__main__":
    main()
