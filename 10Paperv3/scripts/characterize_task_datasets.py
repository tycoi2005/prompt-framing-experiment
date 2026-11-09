from __future__ import annotations

import ast
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "prompt_framing_experiment_results.jsonl").exists():
    RESULTS_DIR = ROOT
    OUT_MD = ROOT / "audits" / "task_dataset_audit.md"
else:
    RESULTS_DIR = ROOT.parent / "02ScalingPhrase" / "results_analysis"
    OUT_MD = ROOT / "task_dataset_audit.md"

LOCAL_CODE_JSON = RESULTS_DIR / "smallmodels" / "problems" / "VNSchoolMathProblems_lite.v0.7.json"
LOCAL_MATH_JSON = RESULTS_DIR / "smallmodels" / "problems" / "VietJack_OnVao10_2026.math.v5.json"
VIETJACK_RAW_CSV = RESULTS_DIR.parent / "localmodel" / "problems" / "vietjack_onvao10_2026" / "questions.csv"
API_CODE_JSON = RESULTS_DIR / "apimodels" / "problems" / "base-mathproblems.bigmodel.v7.python.json"
API_MATH_CSV = RESULTS_DIR / "apimodels" / "problems" / "base-mathproblems.bigmodel.v5.csv"
RESULTS_JSONL = RESULTS_DIR / "prompt_framing_experiment_results.jsonl"

OUT_DIR = ROOT / "analysis"
OUT_SUMMARY_CSV = OUT_DIR / "task_dataset_characterization.csv"
OUT_PER_TASK_CSV = OUT_DIR / "per_task_characterization.csv"


def approx_tokens(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text))


def quartiles(vals: list[float]) -> dict[str, float]:
    s = sorted(float(v) for v in vals)
    n = len(s)
    med = statistics.median(s)
    q1 = statistics.median(s[: n // 2])
    q3 = statistics.median(s[(n + 1) // 2 :])
    return {
        "mean": statistics.mean(s),
        "sd": statistics.stdev(s) if n > 1 else 0.0,
        "median": med,
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "min": s[0],
        "max": s[-1],
    }


def fmt_stat(d: dict[str, float], decimals: int = 1) -> str:
    f = f"{{:.{decimals}f}}"
    return (
        f"{f.format(d['mean'])} (SD {f.format(d['sd'])}; "
        f"med {f.format(d['median'])}, IQR {f.format(d['iqr'])}, "
        f"range {f.format(d['min'])}-{f.format(d['max'])})"
    )


def cyclomatic_complexity(code_str: str) -> int:
    tree = ast.parse(code_str)
    cc = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler)):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            cc += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            cc += 1 + len(node.ifs)
    return cc


def analyze_code_ast(code_str: str) -> dict[str, int | bool]:
    tree = ast.parse(code_str)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    top_func = funcs[0] if funcs else None
    n_params = len(top_func.args.args) if top_func else 0
    has_loop = any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in ast.walk(tree))
    has_branch = any(isinstance(n, (ast.If, ast.IfExp)) for n in ast.walk(tree))
    has_nested_func = len(funcs) > 1
    ast_nodes = sum(1 for _ in ast.walk(tree))
    lines = list(code_str.splitlines())
    sloc = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return {
        "n_params": n_params,
        "has_loop": has_loop,
        "has_branch": has_branch,
        "has_nested_func": has_nested_func,
        "ast_nodes": ast_nodes,
        "loc": len(lines),
        "sloc": len(sloc),
        "cc": cyclomatic_complexity(code_str),
    }


def classify_local_code_topic(text: str, code: str) -> str:
    t = (text + " " + code).lower()
    if any(w in t for w in ["probability", "bayes", "hypergeometric", "random", "gosling", "dice", "card", "ball", "chance", "expired"]):
        return "Probability & combinatorics"
    if any(w in t for w in ["prism", "pyramid", "cylinder", "cone", "sphere", "ellipse", "circle", "triangle", "rectangle", "area", "volume", "distance", "coordinate", "parabola", "plane", "angle", "lantern", "garden", "cube", "tetrahedron"]):
        return "Geometry & spatial optimization"
    if any(w in t for w in ["profit", "cost", "maximum", "minimum", "optimal", "revenue", "combo", "hectare", "raw_material", "yield", "price", "salary", "tax", "interest", "loan"]):
        return "Resource optimization & financial modeling"
    if any(w in t for w in ["matrix", "tsp", "cities", "route", "graph", "path", "schedule", "sequence", "stack"]):
        return "Discrete algorithms & graph/sequence search"
    return "Algebraic & physical rate modeling"


def classify_local_math_topic(prompt: str) -> str:
    t = prompt.lower()
    if any(w in t for w in ["probability", "random", "ball", "card", "dice", "coin", "frequency", "relative frequency", "sample", "chart", "table"]):
        return "Probability & statistics"
    if any(w in t for w in ["triangle", "circle", "radius", "diameter", "chord", "tangent", "angle", "cylinder", "cone", "sphere", "height", "shadow", "area", "perimeter", "volume", "inscribed", "circumscribed", "meter"]):
        return "Geometry, trigonometry & mensuration"
    if any(w in t for w in ["system", "equation", "root", "quadratic", "parabola", "line", "x_1", "x_2", "polynomial", "\\sqrt", "compute"]):
        return "Algebraic equations, roots & radicals"
    return "Applied word problems (rate, cost & linear modeling)"


def classify_api_topic(topics_flat: str) -> str:
    if "Geometry" in topics_flat:
        return "Geometry"
    if "Number Theory" in topics_flat:
        return "Number Theory"
    if "Combinatorics" in topics_flat or "Probability" in topics_flat or "Statistics" in topics_flat:
        return "Combinatorics & Probability"
    return "Algebra & Functions"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    pass_by_task: dict[tuple[str, str], dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
    base_pass_by_task: dict[tuple[str, str], dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))

    with RESULTS_JSONL.open() as f:
        for line in f:
            r = json.loads(line)
            mtype = str(r["modeltype"])
            ttype = str(r["task_type"])
            if mtype == "api":
                var_id = int(r["category_id"])
                tid = int(re.findall(r"\d+", str(r["task_id"]))[-1])
            else:
                b, v = str(r["task_id"]).rsplit("_", 1)
                tid = int(re.findall(r"\d+", str(b))[-1])
                var_id = int(v)
            pass_by_task[(mtype, ttype)][tid].append(int(bool(r["passed"])))
            if var_id == 1:
                base_pass_by_task[(mtype, ttype)][tid].append(int(bool(r["passed"])))

    vj_raw: dict[int, dict[str, str]] = {}
    if VIETJACK_RAW_CSV.exists():
        with VIETJACK_RAW_CSV.open() as f:
            for row in csv.DictReader(f):
                vj_raw[int(row["question_id"])] = row

    local_code = json.loads(LOCAL_CODE_JSON.read_text())
    local_math = json.loads(LOCAL_MATH_JSON.read_text())
    api_code = json.loads(API_CODE_JSON.read_text())
    api_math = list(csv.DictReader(API_MATH_CSV.open()))

    per_task_rows: list[dict[str, object]] = []

    for t in local_code:
        tid = int(t["task_id"])
        ast_info = analyze_code_ast(t["code"])
        topic = classify_local_code_topic(t["text"], t["code"])
        full_spec = t["text"] + "\n\nTest cases:\n" + "\n".join(t.get("test_list", []))
        per_task_rows.append(
            {
                "stratum": "local_code",
                "task_id": tid,
                "difficulty": t.get("difficulty", "unknown"),
                "topic": topic,
                "statement_words": len(t["text"].split()),
                "statement_chars": len(t["text"]),
                "statement_tokens": approx_tokens(t["text"]),
                "full_spec_tokens": approx_tokens(full_spec),
                "input_arity_or_givens": ast_info["n_params"],
                "ref_loc_or_lines": ast_info["loc"],
                "ref_sloc_or_words": ast_info["sloc"],
                "ast_nodes": ast_info["ast_nodes"],
                "cyclomatic_complexity": ast_info["cc"],
                "has_loop": int(bool(ast_info["has_loop"])),
                "has_branch": int(bool(ast_info["has_branch"])),
                "test_count": len(t.get("test_list", [])) + len(t.get("challenge_test_list", [])),
                "overall_pass_rate_pct": statistics.mean(pass_by_task[("local", "code")][tid]) * 100.0,
                "baseline_pass_rate_pct": statistics.mean(base_pass_by_task[("local", "code")][tid]) * 100.0,
            }
        )

    for t in local_math:
        tid = int(t["task_id"])
        raw = vj_raw.get(int(t["source_task_id"]), {})
        sol = raw.get("reason_text", "")
        givens = len(re.findall(r"(?<![a-zA-Z_])\d+(?:[.,]\d+)?", t["prompt"]))
        per_task_rows.append(
            {
                "stratum": "local_math",
                "task_id": tid,
                "difficulty": t.get("difficulty", "unknown"),
                "topic": classify_local_math_topic(t["prompt"]),
                "statement_words": len(t["prompt"].split()),
                "statement_chars": len(t["prompt"]),
                "statement_tokens": approx_tokens(t["prompt"]),
                "full_spec_tokens": approx_tokens(t["prompt"]),
                "input_arity_or_givens": givens,
                "ref_loc_or_lines": len([ln for ln in sol.splitlines() if ln.strip()]),
                "ref_sloc_or_words": len(sol.split()),
                "ast_nodes": 0,
                "cyclomatic_complexity": 0,
                "has_loop": 0,
                "has_branch": 0,
                "test_count": 1,
                "overall_pass_rate_pct": statistics.mean(pass_by_task[("local", "math")][tid]) * 100.0,
                "baseline_pass_rate_pct": statistics.mean(base_pass_by_task[("local", "math")][tid]) * 100.0,
            }
        )

    for idx, (tc, tm) in enumerate(zip(api_code, api_math), start=1):
        tid = int(tc["task_id"])
        ast_info = analyze_code_ast(tc["code"])
        topic = classify_api_topic(tm["topics_flat"])
        full_spec = tc["text"] + "\n\nTest cases:\n" + "\n".join(tc.get("test_list", []))
        per_task_rows.append(
            {
                "stratum": "api_code",
                "task_id": tid,
                "difficulty": tc.get("difficulty", "medium"),
                "topic": topic,
                "statement_words": len(tc["text"].split()),
                "statement_chars": len(tc["text"]),
                "statement_tokens": approx_tokens(tc["text"]),
                "full_spec_tokens": approx_tokens(full_spec),
                "input_arity_or_givens": ast_info["n_params"],
                "ref_loc_or_lines": ast_info["loc"],
                "ref_sloc_or_words": ast_info["sloc"],
                "ast_nodes": ast_info["ast_nodes"],
                "cyclomatic_complexity": ast_info["cc"],
                "has_loop": int(bool(ast_info["has_loop"])),
                "has_branch": int(bool(ast_info["has_branch"])),
                "test_count": len(tc.get("test_list", [])) + len(tc.get("challenge_test_list", [])),
                "overall_pass_rate_pct": statistics.mean(pass_by_task[("api", "code")][tid]) * 100.0,
                "baseline_pass_rate_pct": statistics.mean(base_pass_by_task[("api", "code")][tid]) * 100.0,
            }
        )
        givens = len(re.findall(r"(?<![a-zA-Z_])\d+(?:[.,]\d+)?", tm["problem_markdown"]))
        per_task_rows.append(
            {
                "stratum": "api_math",
                "task_id": idx,
                "difficulty": "medium",
                "topic": topic,
                "statement_words": len(tm["problem_markdown"].split()),
                "statement_chars": len(tm["problem_markdown"]),
                "statement_tokens": approx_tokens(tm["problem_markdown"]),
                "full_spec_tokens": approx_tokens(tm["problem_markdown"]),
                "input_arity_or_givens": givens,
                "ref_loc_or_lines": len([ln for ln in tm["solutions_markdown"].splitlines() if ln.strip()]),
                "ref_sloc_or_words": len(tm["solutions_markdown"].split()),
                "ast_nodes": 0,
                "cyclomatic_complexity": 0,
                "has_loop": 0,
                "has_branch": 0,
                "test_count": 1,
                "overall_pass_rate_pct": statistics.mean(pass_by_task[("api", "math")][idx]) * 100.0,
                "baseline_pass_rate_pct": statistics.mean(base_pass_by_task[("api", "math")][idx]) * 100.0,
            }
        )

    with OUT_PER_TASK_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(per_task_rows[0].keys()))
        writer.writeheader()
        writer.writerows(per_task_rows)

    summary_rows: list[dict[str, object]] = []
    for stratum in ("local_code", "local_math", "api_code", "api_math"):
        sub = [r for r in per_task_rows if r["stratum"] == stratum]
        words_q = quartiles([float(r["statement_words"]) for r in sub])
        chars_q = quartiles([float(r["statement_chars"]) for r in sub])
        toks_q = quartiles([float(r["statement_tokens"]) for r in sub])
        pass_q = quartiles([float(r["overall_pass_rate_pct"]) for r in sub])
        base_q = quartiles([float(r["baseline_pass_rate_pct"]) for r in sub])
        arity_q = quartiles([float(r["input_arity_or_givens"]) for r in sub])
        loc_q = quartiles([float(r["ref_loc_or_lines"]) for r in sub])
        sloc_q = quartiles([float(r["ref_sloc_or_words"]) for r in sub])
        cc_q = quartiles([float(r["cyclomatic_complexity"]) for r in sub])
        ast_q = quartiles([float(r["ast_nodes"]) for r in sub])
        topics = Counter(str(r["topic"]) for r in sub)
        diffs = Counter(str(r["difficulty"]) for r in sub)

        summary_rows.append(
            {
                "stratum": stratum,
                "n_tasks": len(sub),
                "words_summary": fmt_stat(words_q, 1),
                "chars_summary": fmt_stat(chars_q, 1),
                "tokens_summary": fmt_stat(toks_q, 1),
                "arity_or_givens_summary": fmt_stat(arity_q, 1),
                "ref_loc_or_lines_summary": fmt_stat(loc_q, 1),
                "ref_sloc_or_words_summary": fmt_stat(sloc_q, 1),
                "ast_nodes_summary": fmt_stat(ast_q, 1) if "code" in stratum else "N/A",
                "cyclomatic_complexity_summary": fmt_stat(cc_q, 1) if "code" in stratum else "N/A",
                "tasks_with_loops": sum(int(r["has_loop"]) for r in sub) if "code" in stratum else 0,
                "tasks_with_branches": sum(int(r["has_branch"]) for r in sub) if "code" in stratum else 0,
                "tasks_with_cc_gt_1": sum(int(r["cyclomatic_complexity"]) > 1 for r in sub) if "code" in stratum else 0,
                "overall_pass_rate_summary": fmt_stat(pass_q, 1),
                "baseline_pass_rate_summary": fmt_stat(base_q, 1),
                "topic_distribution": "; ".join(f"{k}: {v}" for k, v in topics.most_common()),
                "difficulty_distribution": "; ".join(f"{k}: {v}" for k, v in diffs.most_common()),
            }
        )

    with OUT_SUMMARY_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    md_lines = [
        "# Quantitative Characterization of the Four 50-Task Evaluation Benchmarks",
        "",
        "Generated from the four active 50-task benchmark files and the 14,400-run evaluation dataset (`prompt_framing_experiment_results.jsonl`).",
        "",
        "| Stratum | Tasks | Statement Words | Statement Chars | Tokens | Input Arity / Givens | Ref LOC / Lines | Ref SLOC / Words | Cyclomatic Complexity | Overall Pass Rate (%) |",
        "|---|---:|---|---|---|---|---|---|---|---|",
    ]
    for row in summary_rows:
        md_lines.append(
            f"| {row['stratum']} | {row['n_tasks']} | {row['words_summary']} | {row['chars_summary']} | "
            f"{row['tokens_summary']} | {row['arity_or_givens_summary']} | {row['ref_loc_or_lines_summary']} | "
            f"{row['ref_sloc_or_words_summary']} | {row['cyclomatic_complexity_summary']} | {row['overall_pass_rate_summary']} |"
        )

    OUT_MD.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {OUT_SUMMARY_CSV}")
    print(f"Wrote {OUT_PER_TASK_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
