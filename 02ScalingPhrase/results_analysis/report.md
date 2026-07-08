# Consolidated Results Analysis Report

## Scope

- **14,400 total runs**: 10,800 from 6 local Ollama models + 3,600 from 2 API models
- **50 base tasks** × **18 prompt templates** per task kind per model
- **Two task kinds**: code/Python and math reasoning
- **Three prompt factors**: tone (neutral/polite/aggressive), role framing (no role/role), output format (plaintext/JSON/XML)
- **Outcomes**: pass rate, completion tokens, duration, result-only compliance, error modes

## Data Integrity

| Check | Result |
|---|---|
| Small/local result files | 12 JSONL, 900 rows each |
| API result files | 4 JSONL, 900 rows each |
| Duplicate task keys | 0 |
| Empty responses (small) | 14 (Nemotron code only) |
| Empty responses (API) | 0 |
| Prompt metadata join gaps | 0 |

## Performance Summary

### Small/Local Model Sizes

| Model | Parameters | Ollama Size (GiB) |
|---|---|---|
| nemotron-3-nano:4b | 3.97B | 2.64 |
| deepseek-coder:6.7b | 6.74B | 3.57 |
| qwen2.5:7b | 7.0B | 4.36 |
| mistral:7b-instruct | 7.24B | 4.07 |
| llama3.1:8b | 8.0B | 4.58 |
| gemma2:9b | 9.0B | 5.07 |

Size values are quantized model package sizes from local Ollama manifests, not FP16 memory size.

### Small/Local Models

| Kind | Model | Runs | Pass Rate | Median Duration | Mean Tokens |
|---|---|---|---|---|---|
| code | nemotron-3-nano-4b | 900 | 22.8% | 17.78s | 1646 |
| code | qwen2.5-7b | 900 | 13.2% | 8.75s | 316 |
| code | gemma2-9b | 900 | 11.3% | 5.52s | 175 |
| code | llama3.1-8b | 900 | 5.8% | 11.16s | 394 |
| code | deepseek-coder-6.7b | 900 | 1.1% | 9.04s | 491 |
| code | mistral-7b-instruct | 900 | 0.4% | 9.12s | 366 |
| math | nemotron-3-nano-4b | 900 | 91.2% | 3.15s | 289 |
| math | llama3.1-8b | 900 | 43.2% | 5.09s | 274 |
| math | qwen2.5-7b | 900 | 23.6% | 0.68s | 6 |
| math | gemma2-9b | 900 | 15.2% | 0.80s | 6 |
| math | mistral-7b-instruct | 900 | 7.7% | 0.89s | 79 |
| math | deepseek-coder-6.7b | 900 | 5.7% | 5.35s | 287 |

### API Models

| Kind | Model | Runs | Pass Rate | Median Duration | Mean Tokens |
|---|---|---|---|---|---|
| math | deepseek-v4-flash | 900 | 82.4% | 9.41s | 1127 |
| math | gemini-flash | 900 | 24.1% | 3.40s | 15 |
| python | gemini-flash | 900 | 69.0% | 10.30s | 359 |
| python | deepseek-v4-flash | 900 | 66.7% | 16.12s | 1352 |

## Prompt-Factor Contrasts

### Small/Local Models

| Kind | Factor | Level vs Baseline | Δ Pass Rate | p | Δ Tokens | Δ Duration |
|---|---|---|---|---|---|---|
| code | tone | aggressive vs neutral | 0.0 pp | 1.000 | +4 | +0.01s |
| code | tone | polite vs neutral | −0.5 pp | 0.824 | **+30** | **+1.54s** |
| code | role | role vs no role | −1.0 pp | 0.379 | +15 | +0.16s |
| code | format | JSON vs plaintext | +0.2 pp | 1.000 | −16 | **−0.47s** |
| code | format | XML vs plaintext | +0.8 pp | 0.753 | −21 | **−0.38s** |
| math | tone | aggressive vs neutral | +0.9 pp | 0.542 | +7 | −0.02s |
| math | tone | polite vs neutral | +1.7 pp | 0.268 | +17 | +0.28s |
| math | role | role vs no role | +2.2 pp | 0.081 | +11 | +0.14s |
| math | format | JSON vs plaintext | **−4.2 pp** | **0.006** | **−32** | **−0.61s** |
| math | format | XML vs plaintext | −2.2 pp | 0.156 | +1 | −0.13s |

### API Models

| Kind | Factor | Level vs Baseline | Δ Pass Rate | p | Δ Tokens | Δ Duration |
|---|---|---|---|---|---|---|
| python | format | JSON vs plaintext | **+3.2 pp** | **0.036** | −105 | −0.55s |
| python | format | XML vs plaintext | **+4.8 pp** | **0.004** | −78 | −0.87s |
| math | role | role vs no role | **−2.8 pp** | **0.018** | +83 | −0.14s |

No other API contrasts are significant at α=0.05.

All p-values are uncorrected and should be interpreted as exploratory. Under stricter multiple-comparison correction, marginal findings such as API math role framing would not remain significant.

## Dominant-Model Sensitivity

| Dataset | Kind | Full | Without Dominant Model |
|---|---|---|---|
| Small without Nemotron | code | 9.1% | 6.4% |
| Small without Nemotron | math | 31.1% | 19.1% |
| API without DeepSeek | math | 53.3% | 24.1% |
| API without DeepSeek | python | 67.8% | 69.0% |

## Mediation Analysis

We test whether three output-behavior variables mediate prompt effects on pass rate:
- **Verbosity**: `log(completion_tokens)` — longer responses may indicate more explanation
- **Result-only compliance**: `result_only` flag — local code tasks: extracted code with <15% extra text; API Python tasks: short-response heuristic because extracted code is unavailable; math tasks: response <50 chars (just the answer)
- **Duration**: `log(duration_seconds)` — response latency

Role framing labels differ by task template: code uses "expert persona" and math uses "developer role"; both are analyzed as role vs no role.

### Result-Only Compliance by Model

| Model | Code | Math | Pattern |
|---|---|---|---|
| Llama 3.1 | 100% | 6.6% | Always code-only; math always verbose |
| Qwen 2.5 | 99.9% | 99.8% | Always result-only |
| Gemma 2 | 98.8% | 99.9% | Almost always result-only |
| Nemotron | 92.9% | 99.8% | Mostly result-only |
| Mistral | 44.9% | 46.3% | Variable in both |
| DeepSeek | 0.8% | 0.0% | Almost never result-only |

### Step 1: Prompt Factors Affect Output Behavior

**Code tasks:**

| Factor | log(tokens) | result_only | log(duration) |
|---|---|---|---|
| tone_aggressive | +0.55 (n.s.) | −1.39 (p=0.069) | +0.52 (n.s.) |
| **tone_polite** | **+12.40*** | **−7.00*** | **+10.76*** |
| **role_vs_no_role** | **+3.17*** | −1.15 (p=0.066) | **+2.41*** |
| **format_json** | **−3.46*** | **+4.61*** | **−3.32*** |
| **format_xml** | **−4.10*** | **+7.33*** | **−3.57*** |

**Math tasks:**

| Factor | log(tokens) | result_only | log(duration) |
|---|---|---|---|
| tone_aggressive | +4.39 (p=0.088) | −1.39 (p=0.059) | **+4.24*** |
| **tone_polite** | **+10.97*** | −1.28 (p=0.082) | **+7.51*** |
| **role_vs_no_role** | **+8.86*** | −1.00 (p=0.096) | **+3.98*** |
| **format_json** | **−19.80*** | +0.78 (n.s.) | **−11.16*** |
| format_xml | −1.96 (n.s.) | −0.28 (n.s.) | −1.14 (n.s.) |

For code tasks, tone and format strongly affect result-only compliance. For math tasks, result-only compliance is barely affected by any factor — most models either always produce short answers (Gemma, Qwen, Nemotron) or always produce verbose responses (Llama).

### Step 2: Mediation Decomposition (small/code)

| Factor | Total | +tokens | +res_only | +duration | +all3 |
|---|---|---|---|---|---|
| tone_aggressive | −0.00pp | +0.04pp | −0.02pp | +0.04pp | −0.01pp |
| tone_polite | −0.50pp | +0.33pp | −0.62pp | +0.41pp | +0.17pp |
| role_vs_no_role | −1.04pp | −0.83pp | −1.06pp | −0.83pp | −0.87pp |
| format_json | +0.17pp | −0.06pp | +0.25pp | −0.12pp | +0.06pp |
| format_xml | +0.83pp | +0.56pp | +0.96pp | +0.53pp | +0.82pp |

None of the pooled code effects are significant. For polite tone, tokens and duration flip the coefficient from −0.50pp to +0.17pp.

### Step 2: Mediation Decomposition (small/math)

| Factor | Total | +tokens | +res_only | +duration | +all3 |
|---|---|---|---|---|---|
| tone_aggressive | +0.94pp | +0.71pp | +0.88pp | +0.72pp | +1.45pp |
| tone_polite | +1.67pp | +1.08pp | +1.61pp | +1.26pp | +1.51pp |
| **role_vs_no_role** | **+2.19pp*** | **+1.71pp*** | **+2.14pp*** | **+1.97pp*** | +1.38pp |
| **format_json** | **−4.17pp*** | **−3.11pp*** | **−4.13pp*** | **−3.57pp*** | **−2.84pp*** |
| **format_xml** | **−2.22pp*** | **−2.12pp*** | **−2.24pp*** | **−2.16pp*** | **−2.04pp*** |

Significant effects marked with * are from the fixed-effect LPM used for the mediation decomposition, controlling for model and base task. These p-values are not directly comparable to the earlier contrast table. For math, result_only mediates only 1–7% of any effect — it has almost no mediating role because most models produce consistent response lengths regardless of prompt.

### Key Findings

1. **Result-only compliance works differently across task kinds.** For code tasks, tone and format strongly affect whether models output clean code. For math tasks, result-only compliance is barely affected — most models have fixed response patterns (either always short or always verbose).

2. **Tokens and duration are the main mediators.** For math, they mediate about 20–37% of the role and JSON-format effects, while XML mediation is smaller. For code, they flip the polite tone coefficient from −0.50pp to +0.17pp.

3. **Format has the strongest effect on code compliance** (+4.6pp for JSON, +7.3pp for XML), but most of format's pass-rate effect is direct.

4. **For math, format_json hurts performance** (−4.17pp), and 25% is mediated by reduced verbosity — JSON format suppresses reasoning steps.

5. **The strongest thesis claim**: "Prompt factors significantly change output behavior (verbosity, compliance, latency), but the downstream effect on task performance is largely direct, suggesting prompt framing affects how models reason, not just how they present output."

## Notebook Artifacts

- `notebooks/smallmodels_analysis.executed.ipynb` — small/local models (section 21: mediation)
- `notebooks/apimodels_analysis.executed.ipynb` — API models (mediation section)
- `notebooks/smallmodels_without_nemotron_analysis.executed.ipynb` — sensitivity check
- `notebooks/mediation_analysis.ipynb` — standalone mediation notebook
- `prompt_framing_experiment_results.jsonl` — all 14,400 runs with modeltype, task_type, modelname
