"""Behavioral-adjustment decomposition for the two cloud API strata (RQ4).

The manuscript's primary behavioral-adjustment table covers the local strata,
where both compliance outcomes vary. This script extends the same linear
probability decomposition to the API strata so that RQ4 is reported for all
four strata rather than for local models only.

Two API-specific details are handled explicitly:

* Code-only compliance in the API Python stratum is at ceiling (99.9% of 1,800
  responses satisfy the code-only contract), so the compliance control carries
  no usable variance and is omitted from the joint specification, which then
  adjusts for log tokens and log duration only.
* API math result-only compliance does vary and is included as a control.

Output: ``analysis/manuscript_api_mediation.csv``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recompute_manuscript_tables import (  # noqa: E402
    OUT_DIR,
    PROMPT_TERMS,
    SOURCE_JSONL,
    TERM_LABELS,
    fit_lpm,
    load_dataset,
    write_csv,
)

STRATA = [("api", "code", "API Python"), ("api", "math", "API math")]
FE_COLS = ["modelname", "base_task"]


def api_python_compliance_summary() -> dict[str, object]:
    """Recover code-only compliance for API Python from the stored candidate code.

    The API runner does not persist an ``extracted_code`` field, but it records
    the executed program in ``eval_result.candidate_code``. Applying the same
    operational definition used for the local strata (non-empty code and less
    than 15% non-code text in the raw response) makes the compliance outcome
    computable for the API Python stratum.
    """

    total = 0
    has_code = 0
    compliant = 0
    with SOURCE_JSONL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("modeltype") != "api" or row.get("task_type") != "code":
                continue
            total += 1
            response = str(row.get("response_text") or "")
            code = str((row.get("eval_result") or {}).get("candidate_code") or "")
            if code:
                has_code += 1
            extra_ratio = (len(response) - len(code)) / len(response) if response else 1.0
            if code and extra_ratio < 0.15:
                compliant += 1

    summary = {
        "task_group": "API Python",
        "n_responses": total,
        "n_with_extracted_code": has_code,
        "n_code_only_compliant": compliant,
        "compliance_pct": 100 * compliant / total if total else float("nan"),
        "definition": "non-empty candidate_code and <15% non-code characters in response_text",
    }
    write_csv(
        OUT_DIR / "manuscript_api_compliance_summary.csv",
        [summary],
        [
            "task_group",
            "n_responses",
            "n_with_extracted_code",
            "n_code_only_compliant",
            "compliance_pct",
            "definition",
        ],
    )
    return summary


def stratum_specs(subset: pd.DataFrame) -> dict[str, list[str]]:
    specs: dict[str, list[str]] = {"+tokens": ["log_completion_tokens"]}
    compliance_varies = subset["result_only"].nunique() > 1
    if compliance_varies:
        specs["+compliance"] = ["result_only"]
    specs["+duration"] = ["log_duration"]
    joint = ["log_completion_tokens", "log_duration"]
    if compliance_varies:
        joint.append("result_only")
    specs["+joint"] = joint
    return specs


def main() -> None:
    df = load_dataset()
    compliance = api_python_compliance_summary()
    print(
        "API Python code-only compliance: "
        f"{compliance['n_code_only_compliant']}/{compliance['n_responses']} "
        f"({compliance['compliance_pct']:.2f}%)"
    )
    rows: list[dict[str, object]] = []

    for modeltype, task_type, label in STRATA:
        subset = df[df["modeltype"].eq(modeltype) & df["task_type"].eq(task_type)]
        specs = stratum_specs(subset)
        joint_cols = specs["+joint"]
        joint_spec = "+".join(
            {"log_completion_tokens": "tokens", "log_duration": "duration", "result_only": "compliance"}[c]
            for c in joint_cols
        )
        total_res = fit_lpm(subset, "passed_float", PROMPT_TERMS, FE_COLS)

        for term in PROMPT_TERMS:
            total_coef = total_res[term]["coef"]
            row: dict[str, object] = {
                "task_type": task_type,
                "task_group": label,
                "factor": term,
                "factor_label": TERM_LABELS[term],
                "total_pp": total_res[term]["coef_pp"],
                "total_p": total_res[term]["p_value"],
                "joint_spec": joint_spec,
                "n_observations": len(subset),
                "n_models": subset["modelname"].nunique(),
            }
            for spec_name, controls in specs.items():
                controlled_res = fit_lpm(subset, "passed_float", [*PROMPT_TERMS, *controls], FE_COLS)
                controlled_coef = controlled_res[term]["coef"]
                indirect = total_coef - controlled_coef
                key = spec_name.lstrip("+")
                row[f"{key}_pp"] = controlled_res[term]["coef_pp"]
                row[f"{key}_p"] = controlled_res[term]["p_value"]
                row[f"{key}_attenuation_pct"] = (
                    100 * indirect / total_coef if abs(total_coef) > 1e-10 else ""
                )
            rows.append(row)

    write_csv(
        OUT_DIR / "manuscript_api_mediation.csv",
        rows,
        [
            "task_type",
            "task_group",
            "factor",
            "factor_label",
            "total_pp",
            "total_p",
            "tokens_pp",
            "tokens_p",
            "tokens_attenuation_pct",
            "compliance_pp",
            "compliance_p",
            "compliance_attenuation_pct",
            "duration_pp",
            "duration_p",
            "duration_attenuation_pct",
            "joint_pp",
            "joint_p",
            "joint_attenuation_pct",
            "joint_spec",
            "n_observations",
            "n_models",
        ],
    )

    printable = pd.read_csv(OUT_DIR / "manuscript_api_mediation.csv")
    for row in printable.itertuples():
        print(
            f"{row.task_group:11s} {row.factor_label:15s} total={row.total_pp:+6.2f} "
            f"joint={row.joint_pp:+6.2f} ({row.joint_attenuation_pct:6.1f}%) spec={row.joint_spec}"
        )


if __name__ == "__main__":
    main()
