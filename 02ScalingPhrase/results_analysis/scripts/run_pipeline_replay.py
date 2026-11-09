"""Offline end-to-end replay of the 14,400 stored responses (R1-4).

No new LLM calls are made. Every stored response is pushed through a concrete
downstream consumer so that prompt-induced parsing and compliance failures can
be translated into workflow-level quantities:

    extract -> parse/validate -> execute -> (on failure) retry with reformat

The retry stage cannot be measured from a single-shot dataset, so it is
simulated under an explicit, stated assumption: a reformat retry draws
independently from the same model-task output distribution, whose success
probability is estimated from that model-task's neutral-plaintext reference
cell. Expected values are computed analytically (truncated geometric), not by
random draws.

Reported per stratum and per factor level:

* ``harness_fail_rate``    share of runs that fail the stored (harness) pass
* ``strict_parse_fail``    share that a strict downstream parser cannot extract
* ``recoverable``          share that passed the stored tests but failed strict
                           parsing (i.e. a parser--retry policy could rescue it)
* ``success_r0/r1/r2``     end-to-end success with 0, 1, or 2 retries
* ``calls_per_1k``         expected model calls per 1,000 tasks under R=2
* ``added_latency_pct``    expected extra wall-clock time vs. the single attempt
* ``residual_fail``        share still failing after R=2 retries

Output: ``analysis/manuscript_pipeline_replay.csv`` (stratum x factor level)
"""

from __future__ import annotations

import ast
import math
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recompute_manuscript_tables import (  # noqa: E402
    OUT_DIR,
    load_dataset,
    write_csv,
)

STRATA = [
    ("local", "code", "Local code"),
    ("local", "math", "Local math"),
    ("api", "code", "API Python"),
    ("api", "math", "API math"),
]
FACTOR_LEVELS = [
    ("tone", "neutral"),
    ("tone", "aggressive"),
    ("tone", "polite"),
    ("role_binary", "no role"),
    ("role_binary", "role"),
    ("format", "plaintext"),
    ("format", "json"),
    ("format", "xml"),
]
FENCE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.S)
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?(?:/\d+)?")


def strict_extract_code(text: str) -> str:
    """Downstream parser: fenced block first, else a bare code-looking body."""

    if not text:
        return ""
    match = FENCE.search(text)
    if match:
        body = match.group(1)
    else:
        stripped = text.strip()
        if stripped.startswith(("def ", "import ", "from ")):
            body = stripped
        else:
            return ""
    return body.strip()


def parses(code: str) -> bool:
    if not code:
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def strict_extract_number(text: str) -> bool:
    if not text:
        return False
    return bool(NUMBER.search(text))


def analyse(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    code_mask = out["task_type"].eq("code")
    out["strict_ok"] = False
    out.loc[code_mask, "strict_ok"] = [
        parses(strict_extract_code(t)) for t in out.loc[code_mask, "response_text"]
    ]
    out.loc[~code_mask, "strict_ok"] = [
        strict_extract_number(t) for t in out.loc[~code_mask, "response_text"]
    ]
    out["harness_ok"] = out["passed"].astype(bool)
    out["recoverable"] = out["harness_ok"] & ~out["strict_ok"]
    out["hard_fail"] = ~out["harness_ok"]
    return out


def expected_attempts(p0: float, q: float, retries: int) -> float:
    """Expected calls: one attempt, plus truncated-geometric retries."""

    if retries <= 0:
        return 1.0
    fail0 = 1.0 - p0
    if q <= 0:
        return 1.0 + fail0 * retries
    return 1.0 + fail0 * (1.0 - (1.0 - q) ** retries) / q


def success_after(p0: float, q: float, retries: int) -> float:
    return 1.0 - (1.0 - p0) * (1.0 - q) ** retries


def aggregate_rows(work: pd.DataFrame) -> list[dict[str, object]]:
    """Stratum-level replay totals (all 18 prompt variants pooled)."""

    out: list[dict[str, object]] = []
    for modeltype, task_type, label in STRATA:
        subset = work[work["modeltype"].eq(modeltype) & work["task_type"].eq(task_type)]
        p0 = float(subset["harness_ok"].mean())
        q = float(subset["q_retry"].mean())
        parse_fail = float(1.0 - subset["strict_ok"].mean())
        calls2 = expected_attempts(p0, q, 2)
        latency = float(subset["duration_seconds"].mean())
        added = float((subset["mean_duration"] * (calls2 - 1)).mean())
        out.append(
            {
                "task_group": label,
                "factor": "overall",
                "level": "all variants",
                "n_observations": len(subset),
                "harness_pass_rate": p0,
                "strict_parse_fail_rate": parse_fail,
                "share_of_failures_parse": parse_fail / (1 - p0) if p0 < 1 else 0.0,
                "recoverable_rate": float(subset["recoverable"].mean()),
                "hard_fail_rate": float(subset["hard_fail"].mean()),
                "retry_success_prob": q,
                "end_to_end_r0": p0,
                "end_to_end_r1": success_after(p0, q, 1),
                "end_to_end_r2": success_after(p0, q, 2),
                "residual_fail_r2": 1.0 - success_after(p0, q, 2),
                "calls_per_1k_r2": 1000 * calls2,
                "added_latency_pct_r2": 100 * added / latency if latency > 0 else float("nan"),
            }
        )
    return out


def main() -> None:
    df = load_dataset()
    work = analyse(df)

    # Retry success probability = the model-task neutral/plaintext pass rate.
    reference = (
        work[work["tone"].eq("neutral") & work["role_binary"].eq("no role") & work["format"].eq("plaintext")]
        .groupby(["modeltype", "task_type", "modelname"])["harness_ok"]
        .mean()
    )
    work["q_retry"] = [
        float(reference.loc[(r.modeltype, r.task_type, r.modelname)])
        for r in work.itertuples()
    ]
    work["duration_seconds"] = work["duration_seconds"].clip(lower=0)
    mean_duration = work.groupby(["modeltype", "task_type", "modelname"])["duration_seconds"].transform("mean")
    work["mean_duration"] = mean_duration

    rows: list[dict[str, object]] = []
    for modeltype, task_type, label in STRATA:
        for factor, level in FACTOR_LEVELS:
            subset = work[
                work["modeltype"].eq(modeltype)
                & work["task_type"].eq(task_type)
                & work[factor].eq(level)
            ]
            if subset.empty:
                continue
            p0 = float(subset["harness_ok"].mean())
            q = float(subset["q_retry"].mean())
            parse_fail = float(1.0 - subset["strict_ok"].mean())
            fail_rate = 1.0 - p0
            calls2 = expected_attempts(p0, q, 2)
            added = float((subset["mean_duration"] * (calls2 - 1)).mean())
            base_latency = float(subset["mean_duration"].mean())
            rows.append(
                {
                    "task_group": label,
                    "factor": factor,
                    "level": level,
                    "n_observations": len(subset),
                    "harness_pass_rate": p0,
                    "strict_parse_fail_rate": parse_fail,
                    "share_of_failures_parse": parse_fail / fail_rate if fail_rate > 0 else 0.0,
                    "recoverable_rate": float(subset["recoverable"].mean()),
                    "hard_fail_rate": float(subset["hard_fail"].mean()),
                    "retry_success_prob": q,
                    "end_to_end_r0": p0,
                    "end_to_end_r1": success_after(p0, q, 1),
                    "end_to_end_r2": success_after(p0, q, 2),
                    "residual_fail_r2": 1.0 - success_after(p0, q, 2),
                    "calls_per_1k_r2": 1000 * calls2,
                    "added_latency_pct_r2": 100 * added / base_latency if base_latency > 0 else float("nan"),
                }
            )

    write_csv(
        OUT_DIR / "manuscript_pipeline_replay.csv",
        rows + aggregate_rows(work),
        [
            "task_group",
            "factor",
            "level",
            "n_observations",
            "harness_pass_rate",
            "strict_parse_fail_rate",
            "share_of_failures_parse",
            "recoverable_rate",
            "hard_fail_rate",
            "retry_success_prob",
            "end_to_end_r0",
            "end_to_end_r1",
            "end_to_end_r2",
            "residual_fail_r2",
            "calls_per_1k_r2",
            "added_latency_pct_r2",
        ],
    )

    frame = pd.DataFrame(rows)
    for label in frame["task_group"].unique():
        group = frame[frame["task_group"].eq(label)]
        print(
            f"{label:11s} parse-fail={100 * group['strict_parse_fail_rate'].min():.1f}-"
            f"{100 * group['strict_parse_fail_rate'].max():.1f}%  "
            f"recoverable={100 * group['recoverable_rate'].min():.2f}-"
            f"{100 * group['recoverable_rate'].max():.2f}%  "
            f"E2E R0={100 * group['end_to_end_r0'].min():.1f}-{100 * group['end_to_end_r0'].max():.1f}%  "
            f"R2={100 * group['end_to_end_r2'].min():.1f}-{100 * group['end_to_end_r2'].max():.1f}%  "
            f"calls/1k={group['calls_per_1k_r2'].min():.0f}-{group['calls_per_1k_r2'].max():.0f}"
        )


if __name__ == "__main__":
    main()
