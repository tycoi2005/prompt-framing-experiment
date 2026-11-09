"""Consolidated effect-size ledger for Section 4.8.

This script does not fit any new statistical model. It reads the CSV outputs of the
existing analysis pipeline and consolidates every effect-size claim in Section 4.8
("Effect-Size Reporting and Magnitude Interpretation") into one machine-readable
table plus a human-readable audit.

Inputs (all under ``analysis/``):

- ``mixed_effects_pass.csv``                 main logistic mixed-effects Pass@1 results
- ``mixed_effects_behavior.csv``             linear/logistic mixed-effects behavior results
- ``manuscript_behavior_effects.csv``        descriptive cross-check for behavior effects
- ``manuscript_mediation_decomposition.csv`` behavioral-adjustment decomposition
- ``model_vs_prompt_formal_tests.csv``       eta-squared shares, bootstrap CIs, ratios
- ``local_model_specific_bh.csv``            model-specific BH-corrected contrasts
- ``two_way_factor_interactions.csv``        two-way prompt-factor interactions
- ``factor_by_model_interactions.csv``       factor-by-model omnibus tests

Outputs:

- ``analysis/effect_size_summary.csv``       one row per effect-size claim
- ``effect_size_audit.md``                   formatted audit (or ``audits/`` when run
                                             from ``02ScalingPhrase/results_analysis``)

Only the Python standard library is required.
"""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis"
AUDITS_DIR = ROOT / "audits"
OUT_CSV = ANALYSIS_DIR / "effect_size_summary.csv"
OUT_MD = (AUDITS_DIR if AUDITS_DIR.is_dir() else ROOT) / "effect_size_audit.md"

FIELDS = [
    "section",
    "claim_id",
    "stratum",
    "contrast",
    "effect_metric",
    "estimate",
    "ci_low",
    "ci_high",
    "unit",
    "p_value",
    "source_file",
    "source_locator",
]

ROWS: list[dict[str, str]] = []


def load(name: str) -> list[dict[str, str]]:
    path = ANALYSIS_DIR / name
    if not path.exists():
        raise SystemExit(
            f"Missing input: {path}\n"
            "Run the upstream analysis scripts (see README.md) before this summary."
        )
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


def fp(value: str) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number == 0:
        return "0"
    if abs(number) < 0.001:
        return f"{number:.2e}"
    return f"{number:.3f}"


def add(
    section: str,
    claim_id: str,
    stratum: str,
    contrast: str,
    metric: str,
    estimate: str,
    *,
    ci_low: str = "",
    ci_high: str = "",
    unit: str = "",
    p_value: str = "",
    source_file: str = "",
    source_locator: str = "",
) -> None:
    ROWS.append(
        {
            "section": section,
            "claim_id": claim_id,
            "stratum": stratum,
            "contrast": contrast,
            "effect_metric": metric,
            "estimate": estimate,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "unit": unit,
            "p_value": p_value,
            "source_file": source_file,
            "source_locator": source_locator,
        }
    )


def find(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one row for {criteria}, found {len(matches)}. "
            "Regenerate the upstream analysis CSVs."
        )
    return matches[0]


def model_name(slug: str) -> str:
    return slug.replace("_1_50", "")


def stratum_label(modeltype: str, task_type: str) -> str:
    prefix = "API" if modeltype == "api" else modeltype.title()
    return f"{prefix} {task_type}"


def signed(value: float, unit: str) -> str:
    return f"{value:+.2f} pp" if unit == "pp" else f"{value:+.2f}%"


# --------------------------------------------------------------------------- #
# RQ1: model- versus prompt-framing variance shares
# --------------------------------------------------------------------------- #
formal = load("model_vs_prompt_formal_tests.csv")

for row in formal:
    stratum = row["stratum"]
    locator = f"stratum={stratum}"
    add(
        "4.8-RQ1",
        "rq1_eta2_model",
        stratum,
        "Model",
        "eta_squared",
        fnum(row["eta_sq_model_pct"], 2),
        ci_low=fnum(row["boot_eta_model_ci_lo"], 2),
        ci_high=fnum(row["boot_eta_model_ci_hi"], 2),
        unit="percent",
        source_file="model_vs_prompt_formal_tests.csv",
        source_locator=locator,
    )
    add(
        "4.8-RQ1",
        "rq1_eta2_prompt",
        stratum,
        "Prompt variant",
        "eta_squared",
        fnum(row["eta_sq_prompt_pct"], 2),
        ci_low=fnum(row["boot_eta_prompt_ci_lo"], 2),
        ci_high=fnum(row["boot_eta_prompt_ci_hi"], 2),
        unit="percent",
        source_file="model_vs_prompt_formal_tests.csv",
        source_locator=locator,
    )
    add(
        "4.8-RQ1",
        "rq1_eta2_ratio",
        stratum,
        "Model / prompt",
        "ratio",
        fnum(row["boot_ratio_median"], 2),
        ci_low=fnum(row["boot_ratio_ci_lo"], 2),
        ci_high=fnum(row["boot_ratio_ci_hi"], 2),
        unit="ratio",
        source_file="model_vs_prompt_formal_tests.csv",
        source_locator=locator,
    )


# --------------------------------------------------------------------------- #
# RQ2: Pass@1 contrasts (AME and OR)
# --------------------------------------------------------------------------- #
pass_rows = load("mixed_effects_pass.csv")

for row in pass_rows:
    stratum = row["stratum"]
    contrast = row["contrast"]
    locator = f"stratum={stratum}; factor={row['factor']}"
    add(
        "4.8-RQ2",
        "rq2_pass_ame",
        stratum,
        contrast,
        "AME",
        fnum(row["ame_pp"], 2),
        ci_low=fnum(row["ame_lo_pp"], 2),
        ci_high=fnum(row["ame_hi_pp"], 2),
        unit="pp",
        p_value=fp(row["p_value"]),
        source_file="mixed_effects_pass.csv",
        source_locator=locator,
    )
    add(
        "4.8-RQ2",
        "rq2_pass_or",
        stratum,
        contrast,
        "odds_ratio",
        fnum(row["odds_ratio"], 2),
        ci_low=fnum(row["or_lo"], 2),
        ci_high=fnum(row["or_hi"], 2),
        unit="ratio",
        p_value=fp(row["p_value"]),
        source_file="mixed_effects_pass.csv",
        source_locator=locator,
    )

supported = [
    row
    for row in pass_rows
    if float(row["ame_lo_pp"]) > 0 or float(row["ame_hi_pp"]) < 0
]
null_interval = [row for row in pass_rows if row not in supported]
supported_abs = [abs(float(row["ame_pp"])) for row in supported]
largest_positive = max(pass_rows, key=lambda row: float(row["ame_pp"]))
largest_negative = min(pass_rows, key=lambda row: float(row["ame_pp"]))
largest_null = max(null_interval, key=lambda row: abs(float(row["ame_pp"])))
small_supported = [
    row for row in supported if abs(float(row["ame_pp"])) <= 2.2
]

add(
    "4.8-RQ2",
    "rq2_supported_count",
    "All strata",
    "Pass@1 contrasts with 95% AME intervals excluding zero (OR intervals excluding 1.0)",
    "count",
    str(len(supported)),
    unit="contrasts",
    source_file="mixed_effects_pass.csv",
)
add(
    "4.8-RQ2",
    "rq2_null_interval_count",
    "All strata",
    "Pass@1 contrasts with 95% AME intervals including zero (OR intervals including 1.0)",
    "count",
    str(len(null_interval)),
    unit="contrasts",
    source_file="mixed_effects_pass.csv",
)
add(
    "4.8-RQ2",
    "rq2_supported_abs_ame_min",
    "All strata",
    "Smallest supported |AME|",
    "abs_AME",
    fnum(min(supported_abs), 2),
    unit="pp",
    source_file="mixed_effects_pass.csv",
)
add(
    "4.8-RQ2",
    "rq2_supported_abs_ame_max",
    "All strata",
    "Largest supported |AME|",
    "abs_AME",
    fnum(max(supported_abs), 2),
    unit="pp",
    source_file="mixed_effects_pass.csv",
)
add(
    "4.8-RQ2",
    "rq2_supported_small_ame_count",
    "All strata",
    "Supported contrasts with |AME| <= 2.2 pp",
    "count",
    str(len(small_supported)),
    unit="contrasts",
    source_file="mixed_effects_pass.csv",
)
add(
    "4.8-RQ2",
    "rq2_largest_positive_ame",
    largest_positive["stratum"],
    largest_positive["contrast"],
    "AME",
    fnum(largest_positive["ame_pp"], 2),
    ci_low=fnum(largest_positive["ame_lo_pp"], 2),
    ci_high=fnum(largest_positive["ame_hi_pp"], 2),
    unit="pp",
    p_value=fp(largest_positive["p_value"]),
    source_file="mixed_effects_pass.csv",
    source_locator=f"stratum={largest_positive['stratum']}; factor={largest_positive['factor']}",
)
add(
    "4.8-RQ2",
    "rq2_largest_negative_ame",
    largest_negative["stratum"],
    largest_negative["contrast"],
    "AME",
    fnum(largest_negative["ame_pp"], 2),
    ci_low=fnum(largest_negative["ame_lo_pp"], 2),
    ci_high=fnum(largest_negative["ame_hi_pp"], 2),
    unit="pp",
    p_value=fp(largest_negative["p_value"]),
    source_file="mixed_effects_pass.csv",
    source_locator=f"stratum={largest_negative['stratum']}; factor={largest_negative['factor']}",
)
add(
    "4.8-RQ2",
    "rq2_largest_null_interval_ame",
    largest_null["stratum"],
    largest_null["contrast"],
    "AME",
    fnum(largest_null["ame_pp"], 2),
    ci_low=fnum(largest_null["ame_lo_pp"], 2),
    ci_high=fnum(largest_null["ame_hi_pp"], 2),
    unit="pp",
    p_value=fp(largest_null["p_value"]),
    source_file="mixed_effects_pass.csv",
    source_locator=f"stratum={largest_null['stratum']}; factor={largest_null['factor']}",
)


# --------------------------------------------------------------------------- #
# RQ3: behavioral effect sizes
# --------------------------------------------------------------------------- #
behavior = load("mixed_effects_behavior.csv")
behavior_descriptive = load("manuscript_behavior_effects.csv")

BEHAVIOR_CLAIMS = [
    ("Local code", "log_completion_tokens", "tone_polite", "rq3_local_code_polite_tokens"),
    ("Local code", "log_duration", "tone_polite", "rq3_local_code_polite_duration"),
    ("Local code", "result_only", "tone_polite", "rq3_local_code_polite_compliance"),
    ("Local code", "log_completion_tokens", "format_json", "rq3_local_code_json_tokens"),
    ("Local code", "log_completion_tokens", "format_xml", "rq3_local_code_xml_tokens"),
    ("Local code", "result_only", "format_json", "rq3_local_code_json_compliance"),
    ("Local code", "result_only", "format_xml", "rq3_local_code_xml_compliance"),
    ("Local math", "log_completion_tokens", "format_json", "rq3_local_math_json_tokens"),
    ("Local math", "log_duration", "format_json", "rq3_local_math_json_duration"),
]

for stratum, outcome, factor, claim_id in BEHAVIOR_CLAIMS:
    row = find(behavior, stratum=stratum, outcome=outcome, factor=factor)
    unit = "pp" if row["unit"].startswith("pp") else "percent"
    add(
        "4.8-RQ3",
        claim_id,
        stratum,
        row["contrast"],
        "relative_change" if unit == "percent" else "AME",
        fnum(row["effect_approx"], 2),
        unit=unit,
        p_value=fp(row["p_value"]),
        source_file="mixed_effects_behavior.csv",
        source_locator=f"stratum={stratum}; outcome={outcome}; factor={factor}",
    )


# --------------------------------------------------------------------------- #
# RQ4: behavioral-adjustment attenuation
# --------------------------------------------------------------------------- #
mediation = load("manuscript_mediation_decomposition.csv")

ATTENUATION_CLAIMS = [
    ("Local math", "format_json", "rq4_local_math_json_attenuation"),
    ("Local code", "tone_polite", "rq4_local_code_polite_attenuation"),
]

for task_group, factor, claim_id in ATTENUATION_CLAIMS:
    row = find(mediation, task_group=task_group, factor=factor)
    total = float(row["total_pp"])
    adjusted = float(row["+all3_pp"])
    attenuation = 100.0 * (total - adjusted) / total if total != 0 else float("nan")
    locator = f"task_group={task_group}; factor={factor}"
    add(
        "4.8-RQ4",
        claim_id + "_total",
        task_group,
        row["factor_label"],
        "total_effect",
        fnum(row["total_pp"], 2),
        unit="pp",
        p_value=fp(row["total_p"]),
        source_file="manuscript_mediation_decomposition.csv",
        source_locator=locator,
    )
    add(
        "4.8-RQ4",
        claim_id + "_adjusted",
        task_group,
        row["factor_label"],
        "adjusted_effect",
        fnum(row["+all3_pp"], 2),
        unit="pp",
        source_file="manuscript_mediation_decomposition.csv",
        source_locator=locator,
    )
    add(
        "4.8-RQ4",
        claim_id,
        task_group,
        row["factor_label"],
        "attenuation",
        fnum(attenuation, 2),
        unit="percent",
        source_file="manuscript_mediation_decomposition.csv",
        source_locator=locator + "; 100*(total_pp - adjusted)/total_pp",
    )


# --------------------------------------------------------------------------- #
# RQ5: model-specific and interaction effect sizes
# --------------------------------------------------------------------------- #
local_specific = load("local_model_specific_bh.csv")

MODEL_SPECIFIC_CLAIMS = [
    ("math", "llama3.1-8b", "format", "json", "rq5_llama_math_json"),
    ("math", "llama3.1-8b", "format", "xml", "rq5_llama_math_xml"),
    ("math", "deepseek-coder-6.7b", "format", "xml", "rq5_deepseek_math_xml"),
    ("math", "qwen2.5-7b", "role_binary", "role", "rq5_qwen_math_role"),
]

for kind, model_substr, factor, level, claim_id in MODEL_SPECIFIC_CLAIMS:
    matches = [
        row
        for row in local_specific
        if row["kind"] == kind
        and model_substr in row["model_slug"]
        and row["factor"] == factor
        and row["level"] == level
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one model-specific row for {claim_id}, found {len(matches)}."
        )
    row = matches[0]
    add(
        "4.8-RQ5",
        claim_id,
        f"{kind.title()} / {model_name(row['model_slug'])}",
        f"{row['factor']}={row['level']} vs. {row['baseline']}",
        "delta_pass_rate",
        fnum(row["delta_pass_rate_pp"], 2),
        unit="pp",
        p_value=fp(row["p_value"]),
        source_file="local_model_specific_bh.csv",
        source_locator=f"model={model_name(row['model_slug'])}; factor={factor}; level={level}",
    )

two_way = load("two_way_factor_interactions.csv")
include_zero = [
    row
    for row in two_way
    if float(row["ci95_low_pp"]) <= 0 <= float(row["ci95_high_pp"])
]
add(
    "4.8-RQ5",
    "rq5_two_way_ci_includes_zero",
    "All strata",
    "Two-way prompt-factor interactions",
    "count",
    str(len(include_zero)),
    unit="of 32",
    source_file="two_way_factor_interactions.csv",
)
add(
    "4.8-RQ5",
    "rq5_two_way_global_bh_survivors",
    "All strata",
    "Two-way interactions with q_global32 < 0.05",
    "count",
    str(sum(1 for row in two_way if float(row["q_global32_bh"]) < 0.05)),
    unit="of 32",
    source_file="two_way_factor_interactions.csv",
)
add(
    "4.8-RQ5",
    "rq5_two_way_min_global_q",
    "All strata",
    "Minimum global BH q-value",
    "q_value",
    fnum(min(float(row["q_global32_bh"]) for row in two_way), 3),
    unit="q",
    source_file="two_way_factor_interactions.csv",
)

factor_by_model = load("factor_by_model_interactions.csv")

FACTOR_MODEL_CLAIMS = [
    ("local", "math", "All Factor x Model", "rq5_local_math_factor_model"),
    ("local", "math", "Format x Model", "rq5_local_math_format_model"),
    ("api", "math", "Format x Model", "rq5_api_math_format_model"),
]

for modeltype, task_type, block, claim_id in FACTOR_MODEL_CLAIMS:
    row = find(
        factor_by_model,
        modeltype=modeltype,
        task_type=task_type,
        interaction_block=block,
    )
    add(
        "4.8-RQ5",
        claim_id,
        stratum_label(modeltype, task_type),
        block,
        "omnibus_test",
        fnum(row["wald_f"], 2),
        unit=f"F({row['df']})",
        p_value=fp(row["p_value"]),
        source_file="factor_by_model_interactions.csv",
        source_locator=f"modeltype={modeltype}; task_type={task_type}; block={block}",
    )


# --------------------------------------------------------------------------- #
# Write CSV
# --------------------------------------------------------------------------- #
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(ROWS)


# --------------------------------------------------------------------------- #
# Write markdown audit
# --------------------------------------------------------------------------- #
def md_table(headers: list[str], data: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in data:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return lines


def markdown() -> str:
    lines: list[str] = [
        "# Effect-Size Audit — Section 4.8",
        "",
        "**Generated by:** `scripts/run_effect_size_summary.py`",
        "",
        "This audit consolidates the effect sizes cited in Section 4.8 (\"Effect-Size",
        "Reporting and Magnitude Interpretation\"). No statistical model is re-fitted:",
        "every value is read from an existing analysis CSV, and the two attenuation",
        "percentages are computed from the `total_pp` and `+all3_pp` columns of",
        "`manuscript_mediation_decomposition.csv`.",
        "",
        "## Source files",
        "",
        *md_table(
            ["Source CSV", "Role in Section 4.8"],
            [
                ["`mixed_effects_pass.csv`", "Pass@1 odds ratios, AMEs, 95% intervals"],
                ["`mixed_effects_behavior.csv`", "Token, duration, and compliance effects"],
                ["`manuscript_behavior_effects.csv`", "Descriptive cross-check of behavior effects"],
                ["`manuscript_mediation_decomposition.csv`", "Total vs. behavior-adjusted effects"],
                ["`model_vs_prompt_formal_tests.csv`", "η² shares, bootstrap intervals, ratios"],
                ["`local_model_specific_bh.csv`", "Model-specific BH-corrected Pass@1 contrasts"],
                ["`two_way_factor_interactions.csv`", "Two-way prompt-factor interactions"],
                ["`factor_by_model_interactions.csv`", "Factor × model omnibus tests"],
            ],
        ),
        "",
        "## RQ1 — Model versus prompt variance shares",
        "",
    ]

    rq1_data = []
    for row in formal:
        rq1_data.append(
            [
                row["stratum"],
                f"{float(row['eta_sq_model_pct']):.2f}% "
                f"[{float(row['boot_eta_model_ci_lo']):.2f}, {float(row['boot_eta_model_ci_hi']):.2f}]",
                f"{float(row['eta_sq_prompt_pct']):.2f}% "
                f"[{float(row['boot_eta_prompt_ci_lo']):.2f}, {float(row['boot_eta_prompt_ci_hi']):.2f}]",
                f"{float(row['boot_ratio_median']):.1f}× "
                f"[{float(row['boot_ratio_ci_lo']):.1f}, {float(row['boot_ratio_ci_hi']):.1f}]",
            ]
        )
    lines += md_table(
        ["Stratum", "Model η² (95% CI)", "Prompt η² (95% CI)", "Ratio (95% CI)"],
        rq1_data,
    )
    lines += [
        "",
        "The API Python stratum is the stated exception: model identity explains only",
        f"{float(find(formal, stratum='API Python')['eta_sq_model_pct']):.2f}% of Pass@1",
        "variation there, versus",
        f"{float(find(formal, stratum='API Python')['eta_sq_prompt_pct']):.2f}% for the prompt.",
        "",
        "## RQ2 — Pass@1 effect sizes",
        "",
        f"- {len(supported)} of {len(pass_rows)} contrasts have 95% AME intervals excluding",
        f"  zero (equivalently, OR intervals excluding 1.0); {len(null_interval)} of",
        f"  {len(pass_rows)} include zero.",
        f"- Supported |AMEs| span {min(supported_abs):.1f}–{max(supported_abs):.1f} pp.",
        f"- {len(small_supported)} supported contrasts have |AME| ≤ 2.2 pp.",
        f"- Largest positive AME: {float(largest_positive['ame_pp']):+.2f} pp "
        f"({largest_positive['stratum']}, {largest_positive['contrast']}).",
        f"- Largest negative AME: {float(largest_negative['ame_pp']):+.2f} pp "
        f"({largest_negative['stratum']}, {largest_negative['contrast']}).",
        f"- Largest interval-compatible-with-zero AME: {float(largest_null['ame_pp']):+.2f} pp "
        f"({largest_null['stratum']}, {largest_null['contrast']}, p = {fp(largest_null['p_value'])}).",
        "",
    ]

    rq2_data = []
    for row in pass_rows:
        rq2_data.append(
            [
                row["stratum"],
                row["contrast"],
                f"{float(row['ame_pp']):+.2f} pp "
                f"[{float(row['ame_lo_pp']):+.2f}, {float(row['ame_hi_pp']):+.2f}]",
                f"{float(row['odds_ratio']):.2f} "
                f"[{float(row['or_lo']):.2f}, {float(row['or_hi']):.2f}]",
                fp(row["p_value"]),
            ]
        )
    lines += md_table(
        ["Stratum", "Contrast", "AME (95% CI)", "OR (95% CI)", "p"],
        rq2_data,
    )

    lines += [
        "",
        "## RQ3 — Behavioral effect sizes",
        "",
    ]
    rq3_data = []
    for stratum, outcome, factor, _claim_id in BEHAVIOR_CLAIMS:
        row = find(behavior, stratum=stratum, outcome=outcome, factor=factor)
        unit = "pp" if row["unit"].startswith("pp") else "%"
        rq3_data.append(
            [
                stratum,
                row["contrast"],
                outcome,
                signed(float(row["effect_approx"]), unit),
                fp(row["p_value"]),
            ]
        )
    lines += md_table(
        ["Stratum", "Contrast", "Outcome", "Effect", "p"],
        rq3_data,
    )
    descriptive_metric = {
        "log_completion_tokens": "log(tokens)",
        "log_duration": "log(duration)",
        "result_only": "result_only",
    }
    cross_data = []
    max_pct_diff = 0.0
    max_pp_diff = 0.0
    for stratum, outcome, factor, _claim_id in BEHAVIOR_CLAIMS:
        mixed_row = find(behavior, stratum=stratum, outcome=outcome, factor=factor)
        descriptive_row = find(
            behavior_descriptive,
            task_group=stratum,
            metric=descriptive_metric[outcome],
            factor=factor,
        )
        difference = float(mixed_row["effect_approx"]) - float(descriptive_row["effect"])
        if outcome == "result_only":
            max_pp_diff = max(max_pp_diff, abs(difference))
            unit = "pp"
        else:
            max_pct_diff = max(max_pct_diff, abs(difference))
            unit = "%"
        cross_data.append(
            [
                stratum,
                mixed_row["contrast"],
                outcome,
                signed(float(mixed_row["effect_approx"]), unit),
                signed(float(descriptive_row["effect"]), unit),
                signed(difference, unit),
            ]
        )
    lines += [
        "",
        "### Descriptive cross-check",
        "",
        "The mixed-model estimates above are cross-checked against the descriptive",
        "contrasts in `manuscript_behavior_effects.csv`. The two pipelines use the same",
        "runs but different estimators, so close agreement indicates that the reported",
        "magnitudes are not an artifact of the mixed-model specification.",
        "",
    ]
    lines += md_table(
        ["Stratum", "Contrast", "Outcome", "Mixed model", "Descriptive", "Difference"],
        cross_data,
    )
    lines += [
        "",
        f"Maximum absolute discrepancy: {max_pct_diff:.2f}% for log-token/duration",
        f"outcomes and {max_pp_diff:.2f} pp for compliance.",
        "",
        "The behavior table has no interval columns in either generated CSV; the",
        "interval-bearing inference for these outcomes is in `mixed_effects_behavior.csv`",
        "(standard errors and p-values).",
        "",
        "## RQ4 — Behavioral-adjustment attenuation",
        "",
    ]
    rq4_data = []
    for task_group, factor, _claim_id in ATTENUATION_CLAIMS:
        row = find(mediation, task_group=task_group, factor=factor)
        total = float(row["total_pp"])
        adjusted = float(row["+all3_pp"])
        attenuation = 100.0 * (total - adjusted) / total if total != 0 else float("nan")
        rq4_data.append(
            [
                task_group,
                row["factor_label"],
                f"{total:+.2f} pp",
                f"{adjusted:+.2f} pp",
                f"{attenuation:.1f}%",
                fp(row["total_p"]),
            ]
        )
    lines += md_table(
        ["Stratum", "Contrast", "Total effect", "Adjusted effect", "Attenuation", "p (total)"],
        rq4_data,
    )

    lines += [
        "",
        "Attenuation is computed as `100 × (total − adjusted) / total`; the adjusted",
        "effect is the `+all3_pp` column (tokens + result-only compliance + duration).",
        "",
        "## RQ5 — Model-specific and interaction magnitudes",
        "",
    ]
    rq5_data = []
    for kind, model_substr, factor, level, _claim_id in MODEL_SPECIFIC_CLAIMS:
        row = next(
            row
            for row in local_specific
            if row["kind"] == kind
            and model_substr in row["model_slug"]
            and row["factor"] == factor
            and row["level"] == level
        )
        rq5_data.append(
            [
                f"{kind.title()} / {model_name(row['model_slug'])}",
                f"{row['factor']}={row['level']}",
                f"{float(row['delta_pass_rate_pp']):+.2f} pp",
                fp(row["p_value"]),
                fp(row["bh_q_math"]) if row["bh_q_math"] else "—",
            ]
        )
    lines += md_table(
        ["Stratum / model", "Contrast", "Δ Pass@1", "p", "BH q"],
        rq5_data,
    )
    lines += [
        "",
        f"- Two-way interactions whose 95% CI includes zero: {len(include_zero)} of {len(two_way)}.",
        f"- Two-way interactions with global BH q < 0.05: "
        f"{sum(1 for row in two_way if float(row['q_global32_bh']) < 0.05)} of {len(two_way)}; "
        f"minimum q = {min(float(row['q_global32_bh']) for row in two_way):.3f}.",
        "",
    ]
    factor_model_data = []
    for modeltype, task_type, block, _claim_id in FACTOR_MODEL_CLAIMS:
        row = find(
            factor_by_model,
            modeltype=modeltype,
            task_type=task_type,
            interaction_block=block,
        )
        factor_model_data.append(
            [
                stratum_label(modeltype, task_type),
                block,
                f"F({row['df']}) = {float(row['wald_f']):.2f}",
                fp(row["p_value"]),
            ]
        )
    lines += md_table(
        ["Stratum", "Interaction block", "Omnibus test", "p"],
        factor_model_data,
    )
    lines += [
        "",
        "## Detectability versus magnitude",
        "",
        "The manuscript uses p-values only to assess compatibility with the null. The",
        "derived counts above make the distinction explicit: small but precisely",
        "estimated effects and larger but imprecise effects are both retained in the",
        "ledger rather than ranked by p-value.",
        "",
    ]
    return "\n".join(lines)


OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.write_text(markdown(), encoding="utf-8")

print(f"Wrote {OUT_CSV.relative_to(ROOT)} ({len(ROWS)} rows)")
print(f"Wrote {OUT_MD.relative_to(ROOT)}")
