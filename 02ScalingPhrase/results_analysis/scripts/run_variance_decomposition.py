"""Formal comparison of model effects vs. prompt-framing effects on Pass@1.

For each of the four strata (local/API x code/math) the design is fully crossed and
balanced (models x 50 base tasks x 18 prompt variants, one run per cell). This script
reports four complementary analyses:

1. Balanced ANOVA variance decomposition of Pass@1 into Model, Task, Prompt variant
   (split into Tone, Role, Format main effects and prompt-factor interactions),
   Model x Prompt, Model x Task, Task x Prompt, and residual sums of squares
   (eta-squared shares), with repeated-measures F-tests that treat base task as a
   random blocking factor (each effect is tested against its interaction with task).
2. Task-cluster bootstrap (B resamples of the 50 base tasks) of the difference and
   ratio between the Model and Prompt eta-squared shares.
3. Cluster-robust (CR1, clustered by base task) joint Wald tests of the model block
   versus the prompt block in a linear probability model with both sets of
   fixed effects.
4. Latent-scale (logit) variance partition from a fixed-effects logistic regression
   with model and prompt-factor indicators: Var(model part of the linear predictor)
   versus Var(prompt part), relative to the logistic residual variance pi^2 / 3.

Only the Python standard library is required.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "prompt_framing_experiment_results.jsonl").exists():
    RESULTS_DIR = ROOT
    OUT_MD = ROOT / "audits" / "variance_decomposition_audit.md"
else:
    RESULTS_DIR = ROOT.parent / "02ScalingPhrase" / "results_analysis"
    OUT_MD = ROOT / "variance_decomposition_audit.md"

SOURCE = RESULTS_DIR / "prompt_framing_experiment_results.jsonl"
CODE_TEMPLATE = RESULTS_DIR / "prompt_templates" / "prompt_matrix_prompt_template.09.csv"
MATH_TEMPLATE = RESULTS_DIR / "prompt_templates" / "prompt_matrix_prompt_template.09.math.csv"
OUT_DIR = ROOT / "analysis"
OUT_DECOMP_CSV = OUT_DIR / "model_vs_prompt_variance_decomposition.csv"
OUT_TESTS_CSV = OUT_DIR / "model_vs_prompt_formal_tests.csv"

N_BOOT = 2000
SEED = 20260514
STRATUM_LABELS = {
    ("local", "code"): "Local code",
    ("local", "math"): "Local math",
    ("api", "code"): "API Python",
    ("api", "math"): "API math",
}


# --------------------------------------------------------------------------- #
# Special functions (regularized incomplete beta / gamma) for exact p-values
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def betainc_reg(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(ln_front) * _betacf(a, b, x) / a
    return 1.0 - math.exp(ln_front) * _betacf(b, a, 1.0 - x) / b


def f_sf(f_stat: float, d1: float, d2: float) -> float:
    if f_stat <= 0.0:
        return 1.0
    return betainc_reg(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * f_stat))


def chi2_sf(x: float, k: float) -> float:
    """Upper tail of chi-square via regularized upper incomplete gamma Q(k/2, x/2)."""
    a, z = k / 2.0, x / 2.0
    if z <= 0.0:
        return 1.0
    if z < a + 1.0:
        term = total = 1.0 / a
        n = a
        for _ in range(1000):
            n += 1.0
            term *= z / n
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return max(0.0, 1.0 - total * math.exp(-z + a * math.log(z) - math.lgamma(a)))
    tiny = 1e-300
    b = z + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = d if abs(d) > tiny else tiny
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return math.exp(-z + a * math.log(z) - math.lgamma(a)) * h


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_prompt_metadata() -> dict[tuple[str, int], dict[str, str]]:
    metadata: dict[tuple[str, int], dict[str, str]] = {}
    for task_type, path in (("code", CODE_TEMPLATE), ("math", MATH_TEMPLATE)):
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                metadata[(task_type, int(row["ID"]))] = {
                    "tone": row["Tone"],
                    "role": "role" if row["Role framing"] != "no role" else "no role",
                    "format": row["Format"],
                }
    return metadata


def parse_variant_and_base(row: dict[str, object]) -> tuple[int, str]:
    if row["modeltype"] == "api":
        return int(row["category_id"]), str(row["task_id"])
    base_task, variant = str(row["task_id"]).rsplit("_", 1)
    return int(variant), base_task


def load_strata() -> dict[tuple[str, str], list[dict[str, object]]]:
    metadata = load_prompt_metadata()
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    with SOURCE.open() as handle:
        for line in handle:
            row = json.loads(line)
            task_type = str(row["task_type"])
            variant, base_task = parse_variant_and_base(row)
            groups[(str(row["modeltype"]), task_type)].append(
                {
                    "y": float(bool(row["passed"])),
                    "model": str(row["modelname"]),
                    "task": base_task,
                    "variant": variant,
                    **metadata[(task_type, variant)],
                }
            )
    return groups


# --------------------------------------------------------------------------- #
# 1-2. Balanced ANOVA decomposition and task-cluster bootstrap
# --------------------------------------------------------------------------- #
def build_cube(rows: list[dict[str, object]]):
    models = sorted({str(r["model"]) for r in rows})
    tasks = sorted({str(r["task"]) for r in rows})
    variants = sorted({int(r["variant"]) for r in rows})
    mi = {m: i for i, m in enumerate(models)}
    ti = {t: i for i, t in enumerate(tasks)}
    vi = {v: i for i, v in enumerate(variants)}
    cube = [[[math.nan] * len(variants) for _ in tasks] for _ in models]
    vmeta: dict[int, dict[str, str]] = {}
    for r in rows:
        cube[mi[str(r["model"])]][ti[str(r["task"])]][vi[int(r["variant"])]] = float(r["y"])
        vmeta[vi[int(r["variant"])]] = {"tone": str(r["tone"]), "role": str(r["role"]), "format": str(r["format"])}
    for plane in cube:
        for line in plane:
            if any(math.isnan(v) for v in line):
                raise ValueError("Design is not fully crossed")
    return models, tasks, variants, cube, vmeta


def anova_ss(cube, task_index: list[int], vmeta: dict[int, dict[str, str]]) -> dict[str, float]:
    n_m = len(cube)
    n_v = len(cube[0][0])
    n_t = len(task_index)
    total_n = n_m * n_t * n_v

    m_sum = [0.0] * n_m
    t_sum = [0.0] * n_t
    v_sum = [0.0] * n_v
    mt_sum = [[0.0] * n_t for _ in range(n_m)]
    mv_sum = [[0.0] * n_v for _ in range(n_m)]
    tv_sum = [[0.0] * n_v for _ in range(n_t)]
    sq_sum = 0.0
    for m in range(n_m):
        plane = cube[m]
        for tpos, t in enumerate(task_index):
            line = plane[t]
            for v in range(n_v):
                y = line[v]
                m_sum[m] += y
                t_sum[tpos] += y
                v_sum[v] += y
                mt_sum[m][tpos] += y
                mv_sum[m][v] += y
                tv_sum[tpos][v] += y
                sq_sum += y * y
    grand = sum(m_sum) / total_n
    ss_total = sq_sum - total_n * grand * grand

    m_mean = [s / (n_t * n_v) for s in m_sum]
    t_mean = [s / (n_m * n_v) for s in t_sum]
    v_mean = [s / (n_m * n_t) for s in v_sum]
    ss_m = n_t * n_v * sum((x - grand) ** 2 for x in m_mean)
    ss_t = n_m * n_v * sum((x - grand) ** 2 for x in t_mean)
    ss_v = n_m * n_t * sum((x - grand) ** 2 for x in v_mean)
    ss_mt = n_v * sum(
        (mt_sum[m][t] / n_v - m_mean[m] - t_mean[t] + grand) ** 2 for m in range(n_m) for t in range(n_t)
    )
    ss_mv = n_t * sum(
        (mv_sum[m][v] / n_t - m_mean[m] - v_mean[v] + grand) ** 2 for m in range(n_m) for v in range(n_v)
    )
    ss_tv = n_m * sum(
        (tv_sum[t][v] / n_m - t_mean[t] - v_mean[v] + grand) ** 2 for t in range(n_t) for v in range(n_v)
    )
    ss_resid = ss_total - ss_m - ss_t - ss_v - ss_mt - ss_mv - ss_tv

    # Prompt-factor main effects (orthogonal partitions of SS_variant in the balanced 3x2x3 matrix)
    def factor_ss(key: str) -> float:
        level_sum: dict[str, float] = defaultdict(float)
        level_n: dict[str, int] = defaultdict(int)
        for v in range(n_v):
            level_sum[vmeta[v][key]] += v_sum[v]
            level_n[vmeta[v][key]] += n_m * n_t
        return sum(level_n[k] * (level_sum[k] / level_n[k] - grand) ** 2 for k in level_sum)

    ss_tone = factor_ss("tone")
    ss_role = factor_ss("role")
    ss_format = factor_ss("format")
    return {
        "total": ss_total,
        "model": ss_m,
        "task": ss_t,
        "prompt": ss_v,
        "tone": ss_tone,
        "role": ss_role,
        "format": ss_format,
        "prompt_interactions": ss_v - ss_tone - ss_role - ss_format,
        "model_x_task": ss_mt,
        "model_x_prompt": ss_mv,
        "task_x_prompt": ss_tv,
        "residual": ss_resid,
    }


def tone_role_format_by_task_ss(cube, vmeta) -> dict[str, float]:
    """Factor x Task interaction SS (error terms for the repeated-measures F-tests)."""
    n_m, n_t, n_v = len(cube), len(cube[0]), len(cube[0][0])
    out: dict[str, float] = {}
    grand = sum(cube[m][t][v] for m in range(n_m) for t in range(n_t) for v in range(n_v)) / (n_m * n_t * n_v)
    t_mean = [sum(cube[m][t][v] for m in range(n_m) for v in range(n_v)) / (n_m * n_v) for t in range(n_t)]
    for key in ("tone", "role", "format"):
        levels = sorted({vmeta[v][key] for v in range(n_v)})
        lvl_vs = {lv: [v for v in range(n_v) if vmeta[v][key] == lv] for lv in levels}
        lvl_mean = {
            lv: sum(cube[m][t][v] for m in range(n_m) for t in range(n_t) for v in vs) / (n_m * n_t * len(vs))
            for lv, vs in lvl_vs.items()
        }
        ss = 0.0
        for t in range(n_t):
            for lv, vs in lvl_vs.items():
                cell = sum(cube[m][t][v] for m in range(n_m) for v in vs) / (n_m * len(vs))
                ss += n_m * len(vs) * (cell - lvl_mean[lv] - t_mean[t] + grand) ** 2
        out[key] = ss
        out[f"{key}_levels"] = float(len(levels))
    return out


# --------------------------------------------------------------------------- #
# 3. Cluster-robust LPM block Wald tests
# --------------------------------------------------------------------------- #
def mat_inv(a: list[list[float]]) -> list[list[float]]:
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        div = m[col][col]
        for j in range(2 * n):
            m[col][j] /= div
        for r in range(n):
            if r != col and m[r][col] != 0.0:
                factor = m[r][col]
                for j in range(2 * n):
                    m[r][j] -= factor * m[col][j]
    return [row[n:] for row in m]


def xtx_xty(x: list[list[float]], y: list[float], w: list[float] | None = None):
    k = len(x[0])
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for i, row in enumerate(x):
        wi = 1.0 if w is None else w[i]
        for p in range(k):
            rp = row[p] * wi
            if rp == 0.0:
                continue
            xty[p] += rp * y[i]
            for q in range(k):
                xtx[p][q] += rp * row[q]
    return xtx, xty


def design(rows: list[dict[str, object]], models: list[str]):
    names = ["intercept", "tone_aggressive", "tone_polite", "role", "format_json", "format_xml"] + [
        f"model_{m}" for m in models[1:]
    ]
    x = []
    for r in rows:
        x.append(
            [
                1.0,
                float(r["tone"] == "aggressive"),
                float(r["tone"] == "polite"),
                float(r["role"] == "role"),
                float(r["format"] == "json"),
                float(r["format"] == "xml"),
                *[float(r["model"] == m) for m in models[1:]],
            ]
        )
    return x, names


def cluster_cov(x, resid_score, clusters, bread, n_params, fsc):
    groups: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(clusters):
        groups[c].append(i)
    meat = [[0.0] * n_params for _ in range(n_params)]
    for idxs in groups.values():
        s = [sum(x[i][p] * resid_score[i] for i in idxs) for p in range(n_params)]
        for p in range(n_params):
            for q in range(n_params):
                meat[p][q] += s[p] * s[q]
    tmp = [[sum(bread[p][r] * meat[r][q] for r in range(n_params)) for q in range(n_params)] for p in range(n_params)]
    cov = [[sum(tmp[p][r] * bread[r][q] for r in range(n_params)) * fsc for q in range(n_params)] for p in range(n_params)]
    return cov


def wald(beta, cov, idxs):
    sub = [[cov[i][j] for j in idxs] for i in idxs]
    inv = mat_inv(sub)
    b = [beta[i] for i in idxs]
    k = len(idxs)
    chi2 = sum(b[p] * sum(inv[p][q] * b[q] for q in range(k)) for p in range(k))
    return chi2, k, chi2_sf(chi2, k)


def lpm_block_tests(rows, models):
    x, names = design(rows, models)
    y = [float(r["y"]) for r in rows]
    clusters = [str(r["task"]) for r in rows]
    xtx, xty = xtx_xty(x, y)
    bread = mat_inv(xtx)
    k = len(names)
    beta = [sum(bread[p][q] * xty[q] for q in range(k)) for p in range(k)]
    resid = [y[i] - sum(x[i][p] * beta[p] for p in range(k)) for i in range(len(y))]
    g = len(set(clusters))
    n = len(y)
    fsc = (g / (g - 1.0)) * ((n - 1.0) / (n - k))
    cov = cluster_cov(x, resid, clusters, bread, k, fsc)
    prompt_idx = list(range(1, 6))
    model_idx = list(range(6, k))
    return beta, cov, names, wald(beta, cov, model_idx), wald(beta, cov, prompt_idx)


# --------------------------------------------------------------------------- #
# 4. Latent-scale logistic variance partition
# --------------------------------------------------------------------------- #
def logit_partition(rows, models):
    x, names = design(rows, models)
    y = [float(r["y"]) for r in rows]
    k = len(names)
    beta = [0.0] * k
    for _ in range(50):
        eta = [sum(x[i][p] * beta[p] for p in range(k)) for i in range(len(y))]
        mu = [1.0 / (1.0 + math.exp(-e)) for e in eta]
        w = [max(m * (1.0 - m), 1e-10) for m in mu]
        z = [eta[i] + (y[i] - mu[i]) / w[i] for i in range(len(y))]
        xtx, xtz = xtx_xty(x, z, w)
        new_beta = [sum(row[q] * xtz[q] for q in range(k)) for row in mat_inv(xtx)]
        if max(abs(a - b) for a, b in zip(new_beta, beta)) < 1e-9:
            beta = new_beta
            break
        beta = new_beta

    def variance(vals):
        mean = sum(vals) / len(vals)
        return sum((v - mean) ** 2 for v in vals) / len(vals)

    eta_model = [sum(x[i][p] * beta[p] for p in range(6, k)) for i in range(len(y))]
    eta_prompt = [sum(x[i][p] * beta[p] for p in range(1, 6)) for i in range(len(y))]
    var_m, var_p = variance(eta_model), variance(eta_prompt)
    resid_var = math.pi ** 2 / 3.0
    denom = var_m + var_p + resid_var
    return {
        "var_model_latent": var_m,
        "var_prompt_latent": var_p,
        "share_model_latent": var_m / denom,
        "share_prompt_latent": var_p / denom,
        "ratio_model_to_prompt_latent": var_m / var_p if var_p > 0 else math.inf,
    }


# --------------------------------------------------------------------------- #
def percentile(sorted_vals: list[float], q: float) -> float:
    pos = q * (len(sorted_vals) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    groups = load_strata()

    decomp_rows: list[dict[str, object]] = []
    test_rows: list[dict[str, object]] = []

    for key in (("local", "code"), ("local", "math"), ("api", "code"), ("api", "math")):
        label = STRATUM_LABELS[key]
        rows = groups[key]
        models, tasks, variants, cube, vmeta = build_cube(rows)
        n_m, n_t, n_v = len(models), len(tasks), len(variants)
        ss = anova_ss(cube, list(range(n_t)), vmeta)
        fxt = tone_role_format_by_task_ss(cube, vmeta)

        dfs = {
            "model": n_m - 1,
            "task": n_t - 1,
            "prompt": n_v - 1,
            "tone": 2,
            "role": 1,
            "format": 2,
            "prompt_interactions": n_v - 1 - 5,
            "model_x_task": (n_m - 1) * (n_t - 1),
            "model_x_prompt": (n_m - 1) * (n_v - 1),
            "task_x_prompt": (n_t - 1) * (n_v - 1),
            "residual": (n_m - 1) * (n_t - 1) * (n_v - 1),
        }
        # Repeated-measures error terms (task as random block)
        error_terms = {
            "model": ("model_x_task", ss["model_x_task"], dfs["model_x_task"]),
            "prompt": ("task_x_prompt", ss["task_x_prompt"], dfs["task_x_prompt"]),
            "tone": ("tone_x_task", fxt["tone"], 2 * (n_t - 1)),
            "role": ("role_x_task", fxt["role"], 1 * (n_t - 1)),
            "format": ("format_x_task", fxt["format"], 2 * (n_t - 1)),
            "model_x_prompt": ("residual", ss["residual"], dfs["residual"]),
        }
        for comp in ("model", "task", "prompt", "tone", "role", "format", "prompt_interactions",
                     "model_x_task", "model_x_prompt", "task_x_prompt", "residual"):
            rec: dict[str, object] = {
                "stratum": label,
                "component": comp,
                "df": dfs[comp],
                "sum_sq": ss[comp],
                "eta_sq_pct": 100.0 * ss[comp] / ss["total"],
                "error_term": "",
                "f_stat": "",
                "f_df1": "",
                "f_df2": "",
                "p_value": "",
            }
            if comp in error_terms:
                err_name, err_ss, err_df = error_terms[comp]
                f_stat = (ss[comp] / dfs[comp]) / (err_ss / err_df)
                rec.update(
                    {
                        "error_term": err_name,
                        "f_stat": f_stat,
                        "f_df1": dfs[comp],
                        "f_df2": err_df,
                        "p_value": f_sf(f_stat, dfs[comp], err_df),
                    }
                )
            decomp_rows.append(rec)

        # Task-cluster bootstrap of eta^2 shares
        diffs, ratios, eta_m_b, eta_p_b = [], [], [], []
        for _ in range(N_BOOT):
            idx = [rng.randrange(n_t) for _ in range(n_t)]
            b = anova_ss(cube, idx, vmeta)
            if b["total"] <= 0:
                continue
            em, ep = b["model"] / b["total"], b["prompt"] / b["total"]
            eta_m_b.append(100 * em)
            eta_p_b.append(100 * ep)
            diffs.append(100 * (em - ep))
            ratios.append(em / ep if ep > 0 else math.inf)
        diffs.sort()
        ratios.sort()
        eta_m_b.sort()
        eta_p_b.sort()
        boot_p_one_sided = sum(d <= 0 for d in diffs) / len(diffs)

        beta, cov, names, w_model, w_prompt = lpm_block_tests(rows, models)
        latent = logit_partition(rows, models)

        model_means = [
            100 * sum(cube[m][t][v] for t in range(n_t) for v in range(n_v)) / (n_t * n_v) for m in range(n_m)
        ]
        variant_means = [
            100 * sum(cube[m][t][v] for m in range(n_m) for t in range(n_t)) / (n_m * n_t) for v in range(n_v)
        ]
        test_rows.append(
            {
                "stratum": label,
                "n_obs": n_m * n_t * n_v,
                "n_models": n_m,
                "n_tasks": n_t,
                "n_variants": n_v,
                "model_range_pp": max(model_means) - min(model_means),
                "prompt_variant_range_pp": max(variant_means) - min(variant_means),
                "eta_sq_model_pct": 100 * ss["model"] / ss["total"],
                "eta_sq_prompt_pct": 100 * ss["prompt"] / ss["total"],
                "eta_sq_model_x_prompt_pct": 100 * ss["model_x_prompt"] / ss["total"],
                "eta_sq_task_pct": 100 * ss["task"] / ss["total"],
                "boot_eta_model_ci_lo": percentile(eta_m_b, 0.025),
                "boot_eta_model_ci_hi": percentile(eta_m_b, 0.975),
                "boot_eta_prompt_ci_lo": percentile(eta_p_b, 0.025),
                "boot_eta_prompt_ci_hi": percentile(eta_p_b, 0.975),
                "boot_diff_pp_ci_lo": percentile(diffs, 0.025),
                "boot_diff_pp_ci_hi": percentile(diffs, 0.975),
                "boot_ratio_median": percentile(ratios, 0.5),
                "boot_ratio_ci_lo": percentile(ratios, 0.025),
                "boot_ratio_ci_hi": percentile(ratios, 0.975),
                "boot_p_model_le_prompt": boot_p_one_sided,
                "lpm_wald_model_chi2": w_model[0],
                "lpm_wald_model_df": w_model[1],
                "lpm_wald_model_p": w_model[2],
                "lpm_wald_prompt_chi2": w_prompt[0],
                "lpm_wald_prompt_df": w_prompt[1],
                "lpm_wald_prompt_p": w_prompt[2],
                **latent,
            }
        )

    with OUT_DECOMP_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decomp_rows[0].keys()))
        writer.writeheader()
        writer.writerows(decomp_rows)
    with OUT_TESTS_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(test_rows[0].keys()))
        writer.writeheader()
        writer.writerows(test_rows)

    md = [
        "# Model vs. Prompt Effects: Variance Decomposition and Formal Tests",
        "",
        f"Generated from `prompt_framing_experiment_results.jsonl` (14,400 runs). Bootstrap: {N_BOOT} task-cluster resamples, seed {SEED}.",
        "",
        "## Variance decomposition of Pass@1 (eta-squared, % of total SS) and repeated-measures F-tests",
        "",
        "| Stratum | Component | df | eta^2 (%) | Error term | F | p |",
        "|---|---|---:|---:|---|---:|---:|",
    ]
    for r in decomp_rows:
        f_txt = f"{r['f_stat']:.2f}" if r["f_stat"] != "" else ""
        p_txt = f"{r['p_value']:.3g}" if r["p_value"] != "" else ""
        md.append(
            f"| {r['stratum']} | {r['component']} | {r['df']} | {r['eta_sq_pct']:.2f} | {r['error_term']} | {f_txt} | {p_txt} |"
        )
    md += [
        "",
        "## Model vs. prompt comparison",
        "",
        "| Stratum | Model range (pp) | Prompt-variant range (pp) | eta^2 model [95% CI] | eta^2 prompt [95% CI] | Diff (pp) 95% CI | Ratio median [95% CI] | Boot p (model<=prompt) | LPM Wald model chi2(df), p | LPM Wald prompt chi2(df), p | Latent share model / prompt (%) |",
        "|---|---:|---:|---|---|---|---|---:|---|---|---|",
    ]
    for r in test_rows:
        md.append(
            f"| {r['stratum']} | {r['model_range_pp']:.1f} | {r['prompt_variant_range_pp']:.1f} | "
            f"{r['eta_sq_model_pct']:.2f} [{r['boot_eta_model_ci_lo']:.2f}, {r['boot_eta_model_ci_hi']:.2f}] | "
            f"{r['eta_sq_prompt_pct']:.2f} [{r['boot_eta_prompt_ci_lo']:.2f}, {r['boot_eta_prompt_ci_hi']:.2f}] | "
            f"[{r['boot_diff_pp_ci_lo']:.2f}, {r['boot_diff_pp_ci_hi']:.2f}] | "
            f"{r['boot_ratio_median']:.1f} [{r['boot_ratio_ci_lo']:.1f}, {r['boot_ratio_ci_hi']:.1f}] | "
            f"{r['boot_p_model_le_prompt']:.4f} | "
            f"{r['lpm_wald_model_chi2']:.1f}({r['lpm_wald_model_df']}), {r['lpm_wald_model_p']:.3g} | "
            f"{r['lpm_wald_prompt_chi2']:.1f}({r['lpm_wald_prompt_df']}), {r['lpm_wald_prompt_p']:.3g} | "
            f"{100 * r['share_model_latent']:.2f} / {100 * r['share_prompt_latent']:.2f} |"
        )
    OUT_MD.write_text("\n".join(md) + "\n")
    print(f"Wrote {OUT_DECOMP_CSV}")
    print(f"Wrote {OUT_TESTS_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
