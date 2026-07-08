#!/usr/bin/env python3
"""Analyze local model benchmark JSONL files.

This script intentionally uses only the Python standard library so it can run in
the thesis workspace without installing analysis dependencies.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
OUT_DIR = RESULTS_DIR / "analysis"
PROBLEMS_DIR = ROOT / "problems"
CODE_TEMPLATES_PATH = PROBLEMS_DIR / "prompt_matrix_prompt_template.09.csv"
MATH_TEMPLATES_PATH = PROBLEMS_DIR / "prompt_matrix_prompt_template.09.math.csv"
PILOT_ROOT = ROOT.parent.parent / "01PilotPhrase" / "pivot_problem_dataset"
PILOT_RESULTS_DIR = PILOT_ROOT / "results_codeonly"
PILOT_TEMPLATES_PATH = PILOT_ROOT / "prompt_matrix_prompt_template.08.csv"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def safe_median(values: list[float]) -> float:
    return median(values) if values else 0.0


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def two_proportion_p_value(success_a: int, total_a: int, success_b: int, total_b: int) -> float:
    if total_a == 0 or total_b == 0:
        return 1.0
    pooled = (success_a + success_b) / (total_a + total_b)
    variance = pooled * (1 - pooled) * (1 / total_a + 1 / total_b)
    if variance <= 0:
        return 1.0
    z_score = abs((success_a / total_a - success_b / total_b) / math.sqrt(variance))
    return math.erfc(z_score / math.sqrt(2))


def variant_from_task_id(task_id: str) -> int | None:
    match = re.search(r"_(\d+)$", task_id or "")
    return int(match.group(1)) if match else None


def base_from_task_id(task_id: str) -> str:
    return re.sub(r"_\d+$", "", task_id or "")


def model_slug(path: Path) -> str:
    return path.name.replace(".math.jsonl", "").replace(".jsonl", "")


def normalize_role(role: str) -> str:
    return "role" if role and role.strip().lower() != "no role" else "no role"


def safe_text(value: object) -> str:
    return value if isinstance(value, str) else "" if value is None else str(value)


def error_text(errors: object) -> str:
    if isinstance(errors, list):
        return "\n".join(map(str, errors))
    return safe_text(errors)


def classify_error(errors: object, extracted_code: object = "") -> str:
    text = error_text(errors).lower()
    code = safe_text(extracted_code)
    if extracted_code is not None and not code.strip():
        return "missing_or_empty_code"
    if not text.strip():
        return "none"
    if "not valid python" in text:
        return "invalid_python"
    if "syntax" in text or "invalid syntax" in text:
        return "syntax_error"
    if "not defined" in text or "nameerror" in text:
        return "name_not_defined"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "importerror" in text or "no module named" in text:
        return "import_error"
    if "expected" in text or "assert" in text or "test failed" in text:
        return "wrong_answer"
    return "other_runtime"


def add_behavior_fields(row: dict) -> None:
    response = safe_text(row.get("response_text"))
    code = safe_text(row.get("extracted_code"))
    response_chars = len(response)
    code_chars = len(code)
    extra_text_chars = max(0, response_chars - code_chars)
    row["response_chars"] = response_chars
    row["code_chars"] = code_chars
    row["has_extracted_code"] = int(bool(code.strip()))
    row["extraction_failed"] = int(row.get("kind") == "code" and not code.strip())
    row["extra_text_ratio"] = (extra_text_chars / response_chars) if response_chars else 0.0
    row["likely_code_only"] = int(row.get("kind") == "code" and bool(code.strip()) and row["extra_text_ratio"] < 0.15)
    row["error_category"] = classify_error(row.get("errors"), code if row.get("kind") == "code" else None)
    row["runtime_failure"] = int(row["error_category"] in {"invalid_python", "syntax_error", "name_not_defined", "import_error", "timeout", "other_runtime", "missing_or_empty_code"})


def load_template_metadata() -> dict[tuple[str, int], dict[str, str]]:
    metadata: dict[tuple[str, int], dict[str, str]] = {}
    for kind, path in (("code", CODE_TEMPLATES_PATH), ("math", MATH_TEMPLATES_PATH)):
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                variant_id = int(row["ID"])
                role = row.get("Role framing", "")
                metadata[(kind, variant_id)] = {
                    "tone": row.get("Tone", "").strip() or "unknown",
                    "pressure": row.get("Pressure", "").strip(),
                    "role_framing": role.strip() or "unknown",
                    "role_binary": normalize_role(role),
                    "format": row.get("Format", "").strip() or "unknown",
                }
    return metadata


def read_rows() -> list[dict]:
    rows: list[dict] = []
    template_metadata = load_template_metadata()
    for path in sorted(RESULTS_DIR.glob("*.jsonl")):
        kind = "math" if path.name.endswith(".math.jsonl") else "code"
        slug = model_slug(path)
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                row["_file"] = path.name
                row["_line"] = line_no
                row["kind"] = kind
                row["model_slug"] = slug
                row["model_name"] = row.get("model") or slug
                row["variant_id"] = int(row.get("category_id") or variant_from_task_id(row.get("task_id")) or 0)
                row["base_id"] = row.get("base_task_id") or base_from_task_id(row.get("task_id", ""))
                row.update(template_metadata.get((kind, row["variant_id"]), {}))
                if kind == "code":
                    total = row.get("tests_total") or 0
                    passed = row.get("tests_passed") or 0
                else:
                    total = row.get("values_total") or 0
                    passed = row.get("values_passed") or 0
                row["unit_total"] = int(total)
                row["unit_passed"] = int(passed)
                row["score"] = (passed / total) if total else (1.0 if row.get("passed") else 0.0)
                row["has_error"] = bool(row.get("errors"))
                add_behavior_fields(row)
                rows.append(row)
    return rows


def grouped(rows: list[dict], keys: tuple[str, ...]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


def summarize(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    output = []
    for key_values, items in sorted(grouped(rows, keys).items()):
        successes = sum(1 for row in items if row.get("passed"))
        total = len(items)
        lo, hi = wilson_ci(successes, total)
        record = {key: value for key, value in zip(keys, key_values)}
        record.update(
            {
                "n": total,
                "passed": successes,
                "pass_rate": successes / total if total else 0.0,
                "pass_rate_ci95_low": lo,
                "pass_rate_ci95_high": hi,
                "mean_score": safe_mean([float(row["score"]) for row in items]),
                "median_duration_seconds": safe_median([float(row.get("duration_seconds") or 0) for row in items]),
                "mean_duration_seconds": safe_mean([float(row.get("duration_seconds") or 0) for row in items]),
                "mean_prompt_tokens": safe_mean([float(row.get("prompt_tokens") or 0) for row in items]),
                "mean_completion_tokens": safe_mean([float(row.get("completion_tokens") or 0) for row in items]),
                "error_rate": safe_mean([1.0 if row.get("has_error") else 0.0 for row in items]),
            }
        )
        output.append(record)
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rank_base_tasks(rows: list[dict], kind: str) -> list[dict]:
    output = []
    for (base_id,), items in grouped([row for row in rows if row["kind"] == kind], ("base_id",)).items():
        successes = sum(1 for row in items if row.get("passed"))
        models = len(set(row["model_slug"] for row in items))
        variants = len(set(row["variant_id"] for row in items))
        output.append(
            {
                "kind": kind,
                "base_id": base_id,
                "n": len(items),
                "models": models,
                "variants": variants,
                "pass_rate": successes / len(items) if items else 0.0,
                "mean_score": safe_mean([float(row["score"]) for row in items]),
            }
        )
    return sorted(output, key=lambda item: (item["pass_rate"], item["mean_score"], item["base_id"]))


def solved_by_any_variant(rows: list[dict]) -> list[dict]:
    output = []
    for (model, kind, base_id), items in grouped(rows, ("model_slug", "kind", "base_id")).items():
        output.append(
            {
                "model_slug": model,
                "kind": kind,
                "base_id": base_id,
                "attempts": len(items),
                "any_passed": any(row.get("passed") for row in items),
                "best_score": max(float(row["score"]) for row in items),
            }
        )
    return output


def factor_level_summary(rows: list[dict]) -> list[dict]:
    output = []
    factors = ("tone", "role_binary", "role_framing", "format")
    for group_keys in (("kind",), ("model_slug", "kind")):
        for factor in factors:
            keys = (*group_keys, factor)
            for key_values, items in sorted(grouped(rows, keys).items()):
                successes = sum(1 for row in items if row.get("passed"))
                total = len(items)
                record = {key: value for key, value in zip(keys, key_values)}
                record.update(
                    {
                        "factor": factor,
                        "level": record[factor],
                        "n": total,
                        "passed": successes,
                        "pass_rate": successes / total if total else 0.0,
                        "mean_score": safe_mean([float(row["score"]) for row in items]),
                        "median_duration_seconds": safe_median([float(row.get("duration_seconds") or 0) for row in items]),
                        "mean_prompt_tokens": safe_mean([float(row.get("prompt_tokens") or 0) for row in items]),
                        "mean_completion_tokens": safe_mean([float(row.get("completion_tokens") or 0) for row in items]),
                    }
                )
                output.append(record)
    return output


def behavior_summary(rows: list[dict]) -> list[dict]:
    output = []
    for keys in (
        ("kind",),
        ("kind", "tone"),
        ("kind", "role_binary"),
        ("kind", "format"),
        ("model_slug", "kind"),
        ("model_slug", "kind", "tone"),
        ("model_slug", "kind", "format"),
    ):
        for key_values, items in sorted(grouped(rows, keys).items()):
            record = {key: value for key, value in zip(keys, key_values)}
            record["grouping"] = "+".join(keys)
            record.update(
                {
                    "n": len(items),
                    "pass_rate": safe_mean([1.0 if row.get("passed") else 0.0 for row in items]),
                    "mean_score": safe_mean([float(row["score"]) for row in items]),
                    "mean_completion_tokens": safe_mean([float(row.get("completion_tokens") or 0) for row in items]),
                    "mean_duration_seconds": safe_mean([float(row.get("duration_seconds") or 0) for row in items]),
                    "mean_response_chars": safe_mean([float(row.get("response_chars") or 0) for row in items]),
                    "mean_extra_text_ratio": safe_mean([float(row.get("extra_text_ratio") or 0) for row in items]),
                    "code_only_rate": safe_mean([float(row.get("likely_code_only") or 0) for row in items]),
                    "extraction_failure_rate": safe_mean([float(row.get("extraction_failed") or 0) for row in items]),
                    "runtime_failure_rate": safe_mean([float(row.get("runtime_failure") or 0) for row in items]),
                    "error_rate": safe_mean([1.0 if row.get("has_error") else 0.0 for row in items]),
                }
            )
            output.append(record)
    return output


def error_category_summary(rows: list[dict]) -> list[dict]:
    output = []
    for keys in (("kind", "error_category"), ("kind", "tone", "error_category"), ("model_slug", "kind", "error_category")):
        totals = {key_values: len(items) for key_values, items in grouped(rows, keys[:-1]).items()}
        for key_values, items in sorted(grouped(rows, keys).items()):
            group_key = key_values[:-1]
            record = {key: value for key, value in zip(keys, key_values)}
            record["grouping"] = "+".join(keys)
            record["n"] = len(items)
            record["rate_within_group"] = len(items) / totals[group_key] if totals.get(group_key) else 0.0
            output.append(record)
    return output


def factor_contrasts(rows: list[dict]) -> list[dict]:
    baselines = {
        "tone": "neutral",
        "role_binary": "no role",
        "format": "plaintext",
    }
    output = []
    for group_keys in (("kind",), ("model_slug", "kind")):
        for factor, baseline in baselines.items():
            summaries = summarize(rows, (*group_keys, factor))
            baseline_by_group = {
                tuple(row[key] for key in group_keys): row
                for row in summaries
                if row[factor] == baseline
            }
            for row in summaries:
                group_key = tuple(row[key] for key in group_keys)
                base = baseline_by_group.get(group_key)
                if not base or row[factor] == baseline:
                    continue
                record = {key: row[key] for key in group_keys}
                record.update(
                    {
                        "factor": factor,
                        "baseline": baseline,
                        "level": row[factor],
                        "n": row["n"],
                        "baseline_n": base["n"],
                        "baseline_pass_rate": base["pass_rate"],
                        "level_pass_rate": row["pass_rate"],
                        "delta_pass_rate_pp": (row["pass_rate"] - base["pass_rate"]) * 100,
                        "z_test_p_value": two_proportion_p_value(
                            row["passed"], row["n"], base["passed"], base["n"]
                        ),
                        "baseline_mean_score": base["mean_score"],
                        "level_mean_score": row["mean_score"],
                        "delta_mean_score": row["mean_score"] - base["mean_score"],
                        "baseline_mean_prompt_tokens": base["mean_prompt_tokens"],
                        "level_mean_prompt_tokens": row["mean_prompt_tokens"],
                        "delta_prompt_tokens": row["mean_prompt_tokens"] - base["mean_prompt_tokens"],
                        "baseline_mean_completion_tokens": base["mean_completion_tokens"],
                        "level_mean_completion_tokens": row["mean_completion_tokens"],
                        "delta_completion_tokens": row["mean_completion_tokens"] - base["mean_completion_tokens"],
                        "baseline_mean_duration_seconds": base["mean_duration_seconds"],
                        "level_mean_duration_seconds": row["mean_duration_seconds"],
                        "delta_duration_seconds": row["mean_duration_seconds"] - base["mean_duration_seconds"],
                    }
                )
                output.append(record)
    return output


def factor_interactions(rows: list[dict]) -> list[dict]:
    output = []
    interactions = (
        ("tone", "role_binary"),
        ("tone", "format"),
        ("role_binary", "format"),
    )
    for factor_a, factor_b in interactions:
        keys = ("kind", factor_a, factor_b)
        for key_values, items in sorted(grouped(rows, keys).items()):
            successes = sum(1 for row in items if row.get("passed"))
            total = len(items)
            output.append(
                {
                    "kind": key_values[0],
                    "factor_a": factor_a,
                    "level_a": key_values[1],
                    "factor_b": factor_b,
                    "level_b": key_values[2],
                    "n": total,
                    "passed": successes,
                    "pass_rate": successes / total if total else 0.0,
                    "mean_score": safe_mean([float(row["score"]) for row in items]),
                    "mean_prompt_tokens": safe_mean([float(row.get("prompt_tokens") or 0) for row in items]),
                }
            )
    return output


def paired_fixed_effect_contrasts(rows: list[dict]) -> list[dict]:
    baselines = {
        "tone": "neutral",
        "role_binary": "no role",
        "format": "plaintext",
    }
    output = []
    for factor, baseline in baselines.items():
        score_by_cell = {}
        pass_by_cell = {}
        for row in rows:
            key = (row["model_slug"], row["kind"], row["base_id"], row[factor])
            score_by_cell[key] = float(row["score"])
            pass_by_cell[key] = 1.0 if row.get("passed") else 0.0

        pair_diffs: dict[tuple, list[tuple[float, float]]] = defaultdict(list)
        for row in rows:
            level = row[factor]
            if level == baseline:
                continue
            base_key = (row["model_slug"], row["kind"], row["base_id"], baseline)
            level_key = (row["model_slug"], row["kind"], row["base_id"], level)
            if base_key not in score_by_cell or level_key not in score_by_cell:
                continue
            group_key = (row["kind"], row["model_slug"], factor, baseline, level)
            pair_diffs[group_key].append(
                (
                    score_by_cell[level_key] - score_by_cell[base_key],
                    pass_by_cell[level_key] - pass_by_cell[base_key],
                )
            )

        for (kind, model, factor_name, base, level), diffs in sorted(pair_diffs.items()):
            score_diffs = [diff[0] for diff in diffs]
            pass_diffs = [diff[1] for diff in diffs]
            output.append(
                {
                    "kind": kind,
                    "model_slug": model,
                    "factor": factor_name,
                    "baseline": base,
                    "level": level,
                    "paired_units": len(diffs),
                    "mean_score_delta": safe_mean(score_diffs),
                    "median_score_delta": safe_median(score_diffs),
                    "mean_pass_delta_pp": safe_mean(pass_diffs) * 100,
                    "positive_score_units": sum(1 for value in score_diffs if value > 0),
                    "negative_score_units": sum(1 for value in score_diffs if value < 0),
                    "zero_score_units": sum(1 for value in score_diffs if value == 0),
                }
            )

    overall = []
    for (kind, factor, baseline, level), items in grouped(output, ("kind", "factor", "baseline", "level")).items():
        weights = [item["paired_units"] for item in items]
        total = sum(weights)
        overall.append(
            {
                "kind": kind,
                "model_slug": "ALL_MODELS_FIXED_BY_TASK",
                "factor": factor,
                "baseline": baseline,
                "level": level,
                "paired_units": total,
                "mean_score_delta": sum(item["mean_score_delta"] * item["paired_units"] for item in items) / total if total else 0.0,
                "median_score_delta": "",
                "mean_pass_delta_pp": sum(item["mean_pass_delta_pp"] * item["paired_units"] for item in items) / total if total else 0.0,
                "positive_score_units": sum(item["positive_score_units"] for item in items),
                "negative_score_units": sum(item["negative_score_units"] for item in items),
                "zero_score_units": sum(item["zero_score_units"] for item in items),
            }
        )
    return sorted(overall + output, key=lambda row: (row["kind"], row["factor"], row["level"], row["model_slug"]))


def top_factor_notes(contrasts: list[dict]) -> list[str]:
    kind_rows = [row for row in contrasts if "model_slug" not in row]
    notes = []
    for kind in ("code", "math"):
        rows = [row for row in kind_rows if row["kind"] == kind]
        if not rows:
            continue
        best = max(rows, key=lambda row: row["delta_pass_rate_pp"])
        worst = min(rows, key=lambda row: row["delta_pass_rate_pp"])
        notes.append(
            f"{kind}: largest gain was {best['factor']}={best['level']} "
            f"({best['delta_pass_rate_pp']:+.1f} pp); largest drop was "
            f"{worst['factor']}={worst['level']} ({worst['delta_pass_rate_pp']:+.1f} pp)."
        )
    return notes


def factor_heterogeneity(contrasts: list[dict]) -> list[dict]:
    model_rows = [row for row in contrasts if "model_slug" in row]
    output = []
    for (kind, factor, level), items in sorted(grouped(model_rows, ("kind", "factor", "level")).items()):
        best = max(items, key=lambda row: row["delta_pass_rate_pp"])
        worst = min(items, key=lambda row: row["delta_pass_rate_pp"])
        output.append(
            {
                "kind": kind,
                "factor": factor,
                "level": level,
                "models": len(items),
                "mean_delta_pp": safe_mean([float(row["delta_pass_rate_pp"]) for row in items]),
                "min_delta_pp": worst["delta_pass_rate_pp"],
                "min_model": worst["model_slug"],
                "max_delta_pp": best["delta_pass_rate_pp"],
                "max_model": best["model_slug"],
                "range_delta_pp": best["delta_pass_rate_pp"] - worst["delta_pass_rate_pp"],
                "positive_models": sum(1 for row in items if row["delta_pass_rate_pp"] > 0),
                "negative_models": sum(1 for row in items if row["delta_pass_rate_pp"] < 0),
                "p_lt_0_05_models": sum(1 for row in items if row["z_test_p_value"] < 0.05),
            }
        )
    return sorted(output, key=lambda row: (row["kind"], -row["range_delta_pp"], row["factor"], row["level"]))


def model_factor_winners(rows: list[dict]) -> list[dict]:
    output = []
    for factor in ("tone", "role_binary", "format"):
        summaries = summarize(rows, ("model_slug", "kind", factor))
        for (model, kind), items in grouped(summaries, ("model_slug", "kind")).items():
            best = max(items, key=lambda row: row["pass_rate"])
            worst = min(items, key=lambda row: row["pass_rate"])
            output.append(
                {
                    "model_slug": model,
                    "kind": kind,
                    "factor": factor,
                    "best_level": best[factor],
                    "best_pass_rate": best["pass_rate"],
                    "worst_level": worst[factor],
                    "worst_pass_rate": worst["pass_rate"],
                    "spread_pp": (best["pass_rate"] - worst["pass_rate"]) * 100,
                }
            )
    return sorted(output, key=lambda row: (row["kind"], row["factor"], -row["spread_pp"], row["model_slug"]))


def model_kind_factor_differences(contrasts: list[dict]) -> list[dict]:
    model_rows = [row for row in contrasts if "model_slug" in row]
    by_key = {
        (row["model_slug"], row["factor"], row["level"], row["kind"]): row
        for row in model_rows
    }
    output = []
    seen = sorted(set((row["model_slug"], row["factor"], row["level"]) for row in model_rows))
    for model, factor, level in seen:
        code = by_key.get((model, factor, level, "code"))
        math_row = by_key.get((model, factor, level, "math"))
        if not code or not math_row:
            continue
        output.append(
            {
                "model_slug": model,
                "factor": factor,
                "level": level,
                "code_delta_pp": code["delta_pass_rate_pp"],
                "math_delta_pp": math_row["delta_pass_rate_pp"],
                "math_minus_code_delta_pp": math_row["delta_pass_rate_pp"] - code["delta_pass_rate_pp"],
                "code_baseline_pass_rate": code["baseline_pass_rate"],
                "code_level_pass_rate": code["level_pass_rate"],
                "math_baseline_pass_rate": math_row["baseline_pass_rate"],
                "math_level_pass_rate": math_row["level_pass_rate"],
                "code_p_value": code["z_test_p_value"],
                "math_p_value": math_row["z_test_p_value"],
                "code_delta_prompt_tokens": code["delta_prompt_tokens"],
                "math_delta_prompt_tokens": math_row["delta_prompt_tokens"],
                "math_minus_code_prompt_tokens": math_row["delta_prompt_tokens"] - code["delta_prompt_tokens"],
                "code_delta_completion_tokens": code["delta_completion_tokens"],
                "math_delta_completion_tokens": math_row["delta_completion_tokens"],
                "math_minus_code_completion_tokens": math_row["delta_completion_tokens"] - code["delta_completion_tokens"],
                "code_delta_duration_seconds": code["delta_duration_seconds"],
                "math_delta_duration_seconds": math_row["delta_duration_seconds"],
                "math_minus_code_duration_seconds": math_row["delta_duration_seconds"] - code["delta_duration_seconds"],
            }
        )
    return sorted(output, key=lambda row: (-abs(row["math_minus_code_delta_pp"]), row["model_slug"], row["factor"], row["level"]))


def load_pilot_rows() -> list[dict]:
    if not PILOT_RESULTS_DIR.exists() or not PILOT_TEMPLATES_PATH.exists():
        return []
    template_meta = {}
    with PILOT_TEMPLATES_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            role = row.get("Role framing", "")
            template_meta[int(row["ID"])] = {
                "tone": row.get("Tone", "").strip() or "unknown",
                "role_framing": role.strip() or "unknown",
                "role_binary": normalize_role(role),
                "format": row.get("Format", "").strip() or "unknown",
            }
    rows = []
    for path in sorted(PILOT_RESULTS_DIR.glob("*_1_50.jsonl")):
        slug = path.name.replace("_1_50.jsonl", "")
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                variant_id = variant_from_task_id(row.get("task_id")) or 0
                total = int(row.get("tests_total") or 0)
                passed = int(row.get("tests_passed") or 0)
                row.update(
                    {
                        "dataset": "pilot_codeonly",
                        "kind": "code",
                        "model_slug": slug,
                        "variant_id": variant_id,
                        "base_id": base_from_task_id(row.get("task_id", "")),
                        "unit_total": total,
                        "unit_passed": passed,
                        "score": (passed / total) if total else (1.0 if row.get("passed") else 0.0),
                        "has_error": bool(row.get("errors")),
                        "_file": path.name,
                        "_line": line_no,
                    }
                )
                row.update(template_meta.get(variant_id, {}))
                add_behavior_fields(row)
                rows.append(row)
    return rows


def dataset_shift_summary(current_rows: list[dict]) -> list[dict]:
    pilot_rows = load_pilot_rows()
    comparable_models = {"gemma2-9b", "llama3.1-8b", "qwen2.5-7b"}
    current_code = [
        dict(row, dataset="scaled_common3_code")
        for row in current_rows
        if row["kind"] == "code" and row["model_slug"].replace("_1_50", "") in comparable_models
    ]
    current_all = [dict(row, dataset="scaled_all") for row in current_rows]
    rows = pilot_rows + current_code + current_all
    if not rows:
        return []
    output = []
    for keys in (("dataset",), ("dataset", "kind"), ("dataset", "model_slug"), ("dataset", "kind", "tone"), ("dataset", "kind", "format")):
        for key_values, items in sorted(grouped(rows, keys).items()):
            record = {key: value for key, value in zip(keys, key_values)}
            record["grouping"] = "+".join(keys)
            record.update(
                {
                    "n": len(items),
                    "models": len(set(row["model_slug"] for row in items)),
                    "base_tasks": len(set(row["base_id"] for row in items)),
                    "pass_rate": safe_mean([1.0 if row.get("passed") else 0.0 for row in items]),
                    "mean_score": safe_mean([float(row["score"]) for row in items]),
                    "mean_completion_tokens": safe_mean([float(row.get("completion_tokens") or 0) for row in items]),
                    "mean_duration_seconds": safe_mean([float(row.get("duration_seconds") or 0) for row in items]),
                    "code_only_rate": safe_mean([float(row.get("likely_code_only") or 0) for row in items]),
                    "runtime_failure_rate": safe_mean([float(row.get("runtime_failure") or 0) for row in items]),
                }
            )
            output.append(record)
    return output


def svg_bar_chart(path: Path, title: str, labels: list[str], values: list[float], width: int = 920, height: int = 420) -> None:
    margin_left = 170
    margin_right = 30
    margin_top = 46
    margin_bottom = 36
    inner_w = width - margin_left - margin_right
    inner_h = height - margin_top - margin_bottom
    bar_gap = 8
    bar_h = max(10, (inner_h - bar_gap * (len(labels) - 1)) / max(1, len(labels)))
    max_value = max(values) if values else 1.0
    max_value = max(max_value, 0.01)
    palette = ["#2f6f73", "#c75d4c", "#7c6fbd", "#d89b34", "#3f7fbf", "#67717a"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf7"/>',
        f'<text x="{margin_left}" y="28" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#1d2528">{title}</text>',
    ]
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = margin_top + idx * (bar_h + bar_gap)
        bar_w = inner_w * (value / max_value)
        color = palette[idx % len(palette)]
        lines.extend(
            [
                f'<text x="{margin_left - 12}" y="{y + bar_h * 0.68:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="13" fill="#2c3437">{label}</text>',
                f'<rect x="{margin_left}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{color}"/>',
                f'<text x="{margin_left + bar_w + 8:.1f}" y="{y + bar_h * 0.68:.1f}" font-family="Arial, sans-serif" font-size="13" fill="#2c3437">{pct(value)}</text>',
            ]
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def markdown_table(rows: list[dict], columns: list[str], max_rows: int | None = None) -> str:
    selected = rows[:max_rows] if max_rows else rows
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in selected:
        cells = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                if col.endswith("_pp"):
                    value = f"{value:+.1f} pp"
                elif "rate" in col or col.startswith("pass_"):
                    value = pct(value)
                elif col.startswith("delta_"):
                    value = f"{value:+.2f}"
                elif col.endswith("_p_value"):
                    value = f"{value:.4f}"
                else:
                    value = f"{value:.2f}"
            cells.append(str(value))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, divider, *body])


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = mean(xs)
    mean_y = mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return 0.0
    return numerator / (denom_x * denom_y)


def correlations(rows: list[dict]) -> list[dict]:
    output = []
    for keys in (("kind",), ("model_slug", "kind")):
        for key_values, items in sorted(grouped(rows, keys).items()):
            record = {key: value for key, value in zip(keys, key_values)}
            pass_values = [1.0 if row.get("passed") else 0.0 for row in items]
            scores = [float(row["score"]) for row in items]
            prompt_tokens = [float(row.get("prompt_tokens") or 0) for row in items]
            completion_tokens = [float(row.get("completion_tokens") or 0) for row in items]
            durations = [float(row.get("duration_seconds") or 0) for row in items]
            record.update(
                {
                    "n": len(items),
                    "prompt_tokens_vs_passed": pearson(prompt_tokens, pass_values),
                    "prompt_tokens_vs_score": pearson(prompt_tokens, scores),
                    "completion_tokens_vs_passed": pearson(completion_tokens, pass_values),
                    "completion_tokens_vs_score": pearson(completion_tokens, scores),
                    "duration_vs_passed": pearson(durations, pass_values),
                    "duration_vs_score": pearson(durations, scores),
                }
            )
            output.append(record)
    return output


def write_report(
    rows: list[dict],
    model_kind_summary: list[dict],
    variant_summary: list[dict],
    any_variant: list[dict],
    contrasts: list[dict],
    interactions: list[dict],
    heterogeneity: list[dict],
    factor_winners: list[dict],
    kind_differences: list[dict],
    paired_contrasts: list[dict],
    behavior_rows: list[dict],
    error_rows: list[dict],
    dataset_shift_rows: list[dict],
) -> None:
    report = OUT_DIR / "report.md"
    total_rows = len(rows)
    code_rows = [row for row in rows if row["kind"] == "code"]
    math_rows = [row for row in rows if row["kind"] == "math"]
    models = sorted(set(row["model_slug"] for row in rows))
    base_tasks = sorted(set(row["base_id"] for row in rows))

    by_kind = summarize(rows, ("kind",))
    by_model_overall = summarize(rows, ("model_slug",))
    by_model_overall = sorted(by_model_overall, key=lambda row: row["pass_rate"], reverse=True)
    model_kind_ranked = sorted(model_kind_summary, key=lambda row: (row["kind"], -row["pass_rate"], row["model_slug"]))

    any_summary = summarize(
        [
            {
                "model_slug": row["model_slug"],
                "kind": row["kind"],
                "passed": row["any_passed"],
                "score": row["best_score"],
                "duration_seconds": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "has_error": False,
            }
            for row in any_variant
        ],
        ("model_slug", "kind"),
    )
    any_summary = sorted(any_summary, key=lambda row: (row["kind"], -row["pass_rate"], row["model_slug"]))

    code_tasks = rank_base_tasks(rows, "code")
    math_tasks = rank_base_tasks(rows, "math")
    best_code_variants = sorted([row for row in variant_summary if row["kind"] == "code"], key=lambda row: (-row["pass_rate"], row["variant_id"]))
    worst_code_variants = sorted([row for row in variant_summary if row["kind"] == "code"], key=lambda row: (row["pass_rate"], row["variant_id"]))
    best_math_variants = sorted([row for row in variant_summary if row["kind"] == "math"], key=lambda row: (-row["pass_rate"], row["variant_id"]))
    worst_math_variants = sorted([row for row in variant_summary if row["kind"] == "math"], key=lambda row: (row["pass_rate"], row["variant_id"]))
    corr_rows = correlations(rows)
    contrast_rows = [row for row in contrasts if "model_slug" not in row]
    model_contrast_rows = sorted(
        [row for row in contrasts if "model_slug" in row],
        key=lambda row: (row["kind"], row["factor"], row["level"], -abs(row["delta_pass_rate_pp"]), row["model_slug"]),
    )
    factor_summary_rows = []
    for factor in ("tone", "role_binary", "format"):
        factor_summary_rows.extend(
            sorted(
                [row for row in summarize(rows, ("kind", factor))],
                key=lambda row: (row["kind"], row[factor]),
            )
        )
    interaction_rows = sorted(interactions, key=lambda row: (row["kind"], row["factor_a"], row["factor_b"], -row["pass_rate"]))
    paired_overall = [row for row in paired_contrasts if row["model_slug"] == "ALL_MODELS_FIXED_BY_TASK"]
    behavior_overall = [row for row in behavior_rows if row.get("grouping") in {"kind", "kind+tone", "kind+format", "kind+role_binary"}]
    dataset_shift_overall = [row for row in dataset_shift_rows if row.get("grouping") in {"dataset", "dataset+kind", "dataset+kind+tone", "dataset+kind+format"}]
    error_overall = [row for row in error_rows if row.get("grouping") in {"kind+error_category", "kind+tone+error_category"} and row.get("error_category") != "none"]

    lines = [
        "# Local Model Results Analysis",
        "",
        f"Analyzed `{total_rows}` attempts from `{RESULTS_DIR}`.",
        f"Coverage: `{len(models)}` models, `{len(base_tasks)}` base task ids, `{len(code_rows)}` code attempts, `{len(math_rows)}` math attempts.",
        "",
        "## Overall By Task Type",
        "",
        markdown_table(by_kind, ["kind", "n", "passed", "pass_rate", "mean_score", "median_duration_seconds", "mean_prompt_tokens", "mean_completion_tokens", "error_rate"]),
        "",
        "## Overall By Model",
        "",
        markdown_table(by_model_overall, ["model_slug", "n", "passed", "pass_rate", "mean_score", "median_duration_seconds", "mean_prompt_tokens", "mean_completion_tokens"]),
        "",
        "## Model Ranking Within Each Task Type",
        "",
        markdown_table(model_kind_ranked, ["kind", "model_slug", "n", "passed", "pass_rate", "mean_score", "pass_rate_ci95_low", "pass_rate_ci95_high", "median_duration_seconds"]),
        "",
        "## Base Tasks Solved By At Least One Prompt Variant",
        "",
        markdown_table(any_summary, ["kind", "model_slug", "n", "passed", "pass_rate", "mean_score"]),
        "",
        "## Prompt Factor Main Effects",
        "",
        "Variant metadata comes from the prompt matrix: tone is `neutral`, `polite`, or `aggressive`; role is collapsed to `role` versus `no role`; format is `plaintext`, `json`, or `xml`.",
        "",
        markdown_table(factor_summary_rows, ["kind", "tone" if False else "factor", "n"], max_rows=0) if False else "",
        markdown_table([row | {"factor": "tone", "level": row["tone"]} for row in summarize(rows, ("kind", "tone"))], ["kind", "factor", "level", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"]),
        "",
        markdown_table([row | {"factor": "role", "level": row["role_binary"]} for row in summarize(rows, ("kind", "role_binary"))], ["kind", "factor", "level", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"]),
        "",
        markdown_table([row | {"factor": "format", "level": row["format"]} for row in summarize(rows, ("kind", "format"))], ["kind", "factor", "level", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"]),
        "",
        "## Prompt Factor Contrasts",
        "",
        "Deltas compare each level against the natural baseline within the same task type: neutral tone, no role, and plaintext format. P-values use a simple two-proportion z-test.",
        "",
        markdown_table(contrast_rows, ["kind", "factor", "baseline", "level", "baseline_pass_rate", "level_pass_rate", "delta_pass_rate_pp", "z_test_p_value", "baseline_mean_score", "level_mean_score", "delta_mean_score", "delta_prompt_tokens"]),
        "",
        "## Paired Fixed-Effect-Style Contrasts",
        "",
        "These contrasts compare each factor level against its baseline within the same model, task kind, and base task. This is a dependency-free approximation of fixed effects for model and task difficulty.",
        "",
        markdown_table(paired_overall, ["kind", "model_slug", "factor", "baseline", "level", "paired_units", "mean_score_delta", "mean_pass_delta_pp", "positive_score_units", "negative_score_units", "zero_score_units"]),
        "",
        "## Prompt Factor Interactions",
        "",
        markdown_table(interaction_rows, ["kind", "factor_a", "level_a", "factor_b", "level_b", "n", "passed", "pass_rate", "mean_score"], max_rows=36),
        "",
        "## Model-Specific Factor Behavior",
        "",
        "These rows show where the same prompt factor behaves differently depending on model. `range_delta_pp` is the gap between the most-helped and most-hurt model for that factor level.",
        "",
        markdown_table(heterogeneity, ["kind", "factor", "level", "models", "mean_delta_pp", "min_delta_pp", "min_model", "max_delta_pp", "max_model", "range_delta_pp", "positive_models", "negative_models", "p_lt_0_05_models"], max_rows=24),
        "",
        "## Best Factor Level By Model",
        "",
        markdown_table(factor_winners, ["kind", "model_slug", "factor", "best_level", "best_pass_rate", "worst_level", "worst_pass_rate", "spread_pp"], max_rows=36),
        "",
        "## Math Versus Code Factor Differences",
        "",
        "This compares the same factor level within the same model across task kind. Positive `math_minus_code_delta_pp` means the factor helped math more, or hurt math less, than it helped code. The table also compares prompt-token, completion-token, and duration deltas.",
        "",
        markdown_table(kind_differences, ["model_slug", "factor", "level", "code_delta_pp", "math_delta_pp", "math_minus_code_delta_pp", "math_minus_code_prompt_tokens", "math_minus_code_completion_tokens", "math_minus_code_duration_seconds", "code_p_value", "math_p_value"], max_rows=36),
        "",
        "## Behavior And Error Analysis",
        "",
        "This checks whether prompt factors change output behavior, not only correctness.",
        "",
        markdown_table(behavior_overall, ["grouping", "kind", "tone", "format", "role_binary", "n", "pass_rate", "mean_score", "mean_completion_tokens", "mean_duration_seconds", "code_only_rate", "extraction_failure_rate", "runtime_failure_rate"], max_rows=36),
        "",
        "Frequent non-success error categories:",
        "",
        markdown_table(error_overall, ["grouping", "kind", "tone", "error_category", "n", "rate_within_group"], max_rows=36),
        "",
        "## Dataset Shift: Pilot Versus Scaled Study",
        "",
        "This compares the old 3-model code-only pilot against the scaled study. `scaled_common3_code` keeps only Gemma, Llama, and Qwen code rows to make the closest comparison.",
        "",
        markdown_table(dataset_shift_overall, ["grouping", "dataset", "kind", "tone", "format", "n", "models", "base_tasks", "pass_rate", "mean_score", "mean_completion_tokens", "mean_duration_seconds", "code_only_rate", "runtime_failure_rate"], max_rows=45),
        "",
        "## Model-Specific Factor Contrasts",
        "",
        markdown_table(model_contrast_rows, ["kind", "model_slug", "factor", "baseline", "level", "baseline_pass_rate", "level_pass_rate", "delta_pass_rate_pp", "z_test_p_value"], max_rows=60),
        "",
        "## Factor Takeaways",
        "",
        *[f"- {note}" for note in top_factor_notes(contrasts)],
        "",
        "## Strongest Prompt Variants",
        "",
        "Code:",
        "",
        markdown_table(best_code_variants, ["kind", "variant_id", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"], max_rows=8),
        "",
        "Math:",
        "",
        markdown_table(best_math_variants, ["kind", "variant_id", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"], max_rows=8),
        "",
        "## Weakest Prompt Variants",
        "",
        "Code:",
        "",
        markdown_table(worst_code_variants, ["kind", "variant_id", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"], max_rows=8),
        "",
        "Math:",
        "",
        markdown_table(worst_math_variants, ["kind", "variant_id", "n", "passed", "pass_rate", "mean_score", "mean_prompt_tokens"], max_rows=8),
        "",
        "## Token And Duration Correlations",
        "",
        "Pearson correlations are computed against binary pass/fail and partial-credit score. Values near zero mean little linear relationship.",
        "",
        markdown_table([row for row in corr_rows if "model_slug" not in row], ["kind", "n", "prompt_tokens_vs_passed", "prompt_tokens_vs_score", "completion_tokens_vs_passed", "completion_tokens_vs_score", "duration_vs_passed", "duration_vs_score"]),
        "",
        "## Hardest Base Tasks",
        "",
        "Code:",
        "",
        markdown_table(code_tasks, ["kind", "base_id", "n", "pass_rate", "mean_score"], max_rows=10),
        "",
        "Math:",
        "",
        markdown_table(math_tasks, ["kind", "base_id", "n", "pass_rate", "mean_score"], max_rows=10),
        "",
        "## Easiest Base Tasks",
        "",
        "Code:",
        "",
        markdown_table(list(reversed(code_tasks)), ["kind", "base_id", "n", "pass_rate", "mean_score"], max_rows=10),
        "",
        "Math:",
        "",
        markdown_table(list(reversed(math_tasks)), ["kind", "base_id", "n", "pass_rate", "mean_score"], max_rows=10),
        "",
        "## Artifacts",
        "",
        "- `summary_by_kind.csv`",
        "- `summary_by_model.csv`",
        "- `summary_by_model_and_kind.csv`",
        "- `summary_by_variant.csv`",
        "- `summary_by_model_variant.csv`",
        "- `prompt_factor_summary.csv`",
        "- `prompt_factor_contrasts.csv`",
        "- `prompt_factor_interactions.csv`",
        "- `prompt_factor_heterogeneity.csv`",
        "- `model_factor_winners.csv`",
        "- `model_kind_factor_differences.csv`",
        "- `paired_fixed_effect_contrasts.csv`",
        "- `behavior_summary.csv`",
        "- `error_category_summary.csv`",
        "- `dataset_shift_summary.csv`",
        "- `token_outcome_correlations.csv`",
        "- `base_task_summary.csv`",
        "- `any_variant_summary.csv`",
        "- `pass_rate_by_model.svg`",
        "- `pass_rate_by_model_and_kind.svg`",
        "- `important_insights_analysis.ipynb`",
        "- `important_insights_analysis.executed.ipynb`",
        "- `without_nemotron_analysis.ipynb`",
        "- `without_nemotron_analysis.executed.ipynb`",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows()

    summary_by_kind = summarize(rows, ("kind",))
    summary_by_model = summarize(rows, ("model_slug",))
    summary_by_model_kind = summarize(rows, ("model_slug", "kind"))
    summary_by_variant = summarize(rows, ("kind", "variant_id"))
    summary_by_model_variant = summarize(rows, ("model_slug", "kind", "variant_id"))
    base_task_summary = rank_base_tasks(rows, "code") + rank_base_tasks(rows, "math")
    any_variant = solved_by_any_variant(rows)
    correlation_summary = correlations(rows)
    prompt_factor_summary = factor_level_summary(rows)
    prompt_factor_contrasts = factor_contrasts(rows)
    prompt_factor_interactions = factor_interactions(rows)
    prompt_factor_heterogeneity = factor_heterogeneity(prompt_factor_contrasts)
    model_factor_winner_rows = model_factor_winners(rows)
    model_kind_factor_difference_rows = model_kind_factor_differences(prompt_factor_contrasts)
    paired_fixed_effect_rows = paired_fixed_effect_contrasts(rows)
    behavior_rows = behavior_summary(rows)
    error_rows = error_category_summary(rows)
    dataset_shift_rows = dataset_shift_summary(rows)

    write_csv(OUT_DIR / "summary_by_kind.csv", summary_by_kind)
    write_csv(OUT_DIR / "summary_by_model.csv", summary_by_model)
    write_csv(OUT_DIR / "summary_by_model_and_kind.csv", summary_by_model_kind)
    write_csv(OUT_DIR / "summary_by_variant.csv", summary_by_variant)
    write_csv(OUT_DIR / "summary_by_model_variant.csv", summary_by_model_variant)
    write_csv(OUT_DIR / "prompt_factor_summary.csv", prompt_factor_summary)
    write_csv(OUT_DIR / "prompt_factor_contrasts.csv", prompt_factor_contrasts)
    write_csv(OUT_DIR / "prompt_factor_interactions.csv", prompt_factor_interactions)
    write_csv(OUT_DIR / "prompt_factor_heterogeneity.csv", prompt_factor_heterogeneity)
    write_csv(OUT_DIR / "model_factor_winners.csv", model_factor_winner_rows)
    write_csv(OUT_DIR / "model_kind_factor_differences.csv", model_kind_factor_difference_rows)
    write_csv(OUT_DIR / "paired_fixed_effect_contrasts.csv", paired_fixed_effect_rows)
    write_csv(OUT_DIR / "behavior_summary.csv", behavior_rows)
    write_csv(OUT_DIR / "error_category_summary.csv", error_rows)
    write_csv(OUT_DIR / "dataset_shift_summary.csv", dataset_shift_rows)
    write_csv(OUT_DIR / "token_outcome_correlations.csv", correlation_summary)
    write_csv(OUT_DIR / "base_task_summary.csv", base_task_summary)
    write_csv(OUT_DIR / "any_variant_summary.csv", any_variant)

    overall_rank = sorted(summary_by_model, key=lambda row: row["pass_rate"], reverse=True)
    svg_bar_chart(
        OUT_DIR / "pass_rate_by_model.svg",
        "Overall pass rate by model",
        [row["model_slug"] for row in overall_rank],
        [row["pass_rate"] for row in overall_rank],
    )

    kind_rows = sorted(summary_by_model_kind, key=lambda row: (row["kind"], -row["pass_rate"], row["model_slug"]))
    svg_bar_chart(
        OUT_DIR / "pass_rate_by_model_and_kind.svg",
        "Pass rate by model and task type",
        [f"{row['kind']} / {row['model_slug']}" for row in kind_rows],
        [row["pass_rate"] for row in kind_rows],
        height=620,
    )

    write_report(
        rows,
        summary_by_model_kind,
        summary_by_variant,
        any_variant,
        prompt_factor_contrasts,
        prompt_factor_interactions,
        prompt_factor_heterogeneity,
        model_factor_winner_rows,
        model_kind_factor_difference_rows,
        paired_fixed_effect_rows,
        behavior_rows,
        error_rows,
        dataset_shift_rows,
    )
    print(f"Wrote analysis to {OUT_DIR}")


if __name__ == "__main__":
    main()
