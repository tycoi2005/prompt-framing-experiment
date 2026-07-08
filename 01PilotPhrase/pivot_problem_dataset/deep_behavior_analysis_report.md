# Deep Behavior Analysis Report

Based on `deep_behavior_analysis.py`.

## Purpose

This analysis checks whether the tone effect from the current 2,700-run experiment remains after accounting for output behavior:

- output length (`completion_tokens`)
- code-only compliance (`likely_code_only`)
- code extraction/parsing failure (`extraction_failed`)
- runtime (`duration_seconds`)

The goal is to move the interpretation from:

> Neutral prompts perform better.

to:

> Neutral prompts perform better largely because they change output behavior: they produce shorter, cleaner, more code-focused responses that are easier for the evaluator to execute.

## Data

- Models: 3 (`gemma2-9b`, `llama3.1-8b`, `qwen2.5-7b`)
- Problems: 50
- Prompt templates: 18
- Total runs: 2,700
- Prompt factors: `Tone`, `Role_framing`, `Format`

Outputs are saved under:

`analysis_outputs/deep_behavior/`

## Descriptive Results

Tone changes behavior strongly.

| Tone | Pass rate | Avg. tests passed | Avg. completion tokens | Avg. duration | Code-only rate | Extraction failure rate | Runtime failure rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutral | 10.9% | 15.4% | 413 | 12.62s | 62.3% | 7.1% | 42.3% |
| polite | 8.0% | 11.2% | 716 | 21.47s | 1.4% | 0.1% | 54.3% |
| aggressive | 7.9% | 10.8% | 687 | 20.40s | 0.7% | 3.9% | 53.2% |

The largest behavioral difference is not a small style shift. Neutral prompts produce much shorter outputs and much more code-only output. Polite and aggressive prompts produce more extra prose/wrapper text and much lower code-only compliance.

## Regression Strategy

The main robustness check uses fixed-effect OLS models with model and problem fixed effects:

`outcome ~ Tone + Role_framing + Format + model fixed effects + problem fixed effects + behavior controls`

Two outcomes are analyzed:

- `passed_int`: exact pass/fail
- `tests_fraction`: fraction of tests passed

The baseline model has prompt factors only. Follow-up models add behavior controls:

- `M0_prompt_only`
- `M1_length`: adds log completion tokens
- `M2_code_only`: adds likely code-only response
- `M3_extraction`: adds extraction failure
- `M4_runtime`: adds log runtime
- `M5_all_behavior_controls`: adds all behavior controls

Logistic GLM models were also run for `passed_int` as a robustness check.

## Key Finding: The Neutral Effect Mostly Disappears After Behavior Controls

With aggressive tone as the reference category:

| Outcome | Model | Neutral coefficient | p-value | Interpretation |
|---|---|---:|---:|---|
| pass/fail | Prompt factors only | +3.0 pp | 0.012 | Neutral is significantly better before behavior controls |
| pass/fail | + output length | -2.0 pp | 0.199 | Neutral no longer significant |
| pass/fail | + code-only | +0.7 pp | 0.646 | Neutral no longer significant |
| pass/fail | + extraction failure | +3.2 pp | 0.008 | Neutral remains significant |
| pass/fail | + runtime | -1.6 pp | 0.293 | Neutral no longer significant |
| pass/fail | all behavior controls | -1.9 pp | 0.219 | Neutral no longer significant |

For `tests_fraction`, the same pattern is stronger:

| Outcome | Model | Neutral coefficient | p-value | Interpretation |
|---|---|---:|---:|---|
| tests fraction | Prompt factors only | +4.6 pp | 0.0003 | Neutral is significantly better before behavior controls |
| tests fraction | + output length | -0.9 pp | 0.570 | Neutral no longer significant |
| tests fraction | + code-only | +1.5 pp | 0.338 | Neutral no longer significant |
| tests fraction | + extraction failure | +5.0 pp | 0.0001 | Neutral remains significant |
| tests fraction | + runtime | -0.6 pp | 0.724 | Neutral no longer significant |
| tests fraction | all behavior controls | -0.9 pp | 0.603 | Neutral no longer significant |

This supports a mediation-style interpretation: the observed tone effect is largely explained by output behavior, especially verbosity/runtime and code-only compliance.

## Behavior Controls Matter

In separate fixed-effect models:

- longer outputs are associated with lower correctness
- longer runtime is associated with lower correctness
- code-only responses are associated with higher correctness
- extraction failures are associated with lower correctness

For `tests_fraction`:

| Control | Coefficient | p-value |
|---|---:|---:|
| log completion tokens | -9.9 pp | < 0.001 |
| code-only response | +5.0 pp | 0.0075 |
| extraction failure | -11.1 pp | < 0.001 |
| log runtime | -10.7 pp | < 0.001 |

When all behavior controls are included together, completion tokens and duration become hard to interpret separately because they are almost perfectly correlated (`r = 0.985`). This means the combined model should be treated as a robustness check, not as a clean causal decomposition of length versus runtime.

## Logistic Robustness Check

The logistic GLM results for pass/fail show the same qualitative pattern:

- baseline neutral-tone effect is significant
- after controlling for output length or runtime, the neutral-tone coefficient is no longer significant
- after all behavior controls, neutral tone remains non-significant

This supports the OLS findings and reduces concern that the result is only an artifact of using a linear probability model.

## Model-Specific Pattern

The result is strongest for `gemma2-9b` and `qwen2.5-7b`.

| Model | Best tone by tests fraction | Neutral code-only rate |
|---|---|---:|
| gemma2-9b | neutral | 77.7% |
| qwen2.5-7b | neutral | 79.0% |
| llama3.1-8b | polite, slightly | 30.3% |

The Llama result is a useful caveat. Neutral prompts were not clearly best for Llama, partly because Llama had unusually high extraction failure under neutral prompts. This means the paper should avoid claiming that neutral tone universally improves every model.

Better wording:

> Neutral tone produced the strongest overall result, but the effect is mediated by output behavior and varies across model families.

## Difficulty Split

Problems were split into hard/medium/easy bands based on average test performance across all runs.

| Difficulty | Neutral tests fraction | Polite tests fraction | Aggressive tests fraction |
|---|---:|---:|---:|
| hard | 0.3% | 0.1% | 0.1% |
| medium | 11.5% | 5.5% | 6.5% |
| easy | 34.2% | 27.6% | 25.5% |

Neutral tone is most useful in the medium and easy bands. On the hardest problems, all models are near zero, so prompt tone cannot rescue tasks that are beyond the model/problem setup.

## Error Modes

The dominant failure categories are wrong answers and missing function/name errors.

| Tone | Most common failure pattern |
|---|---|
| neutral | wrong answer, then name-not-defined |
| polite | name-not-defined, then wrong answer |
| aggressive | name-not-defined, then wrong answer |

Polite and aggressive tones produce more `name_not_defined` failures, which suggests that verbose or wrapped outputs may interfere with the expected function-level evaluation.

## Empty Extraction Audit

The result files contain 100 runs where `extracted_code` is empty:

- `llama3.1-8b`: 97 cases
- `qwen2.5-7b`: 3 cases
- `gemma2-9b`: 0 cases

I audited the raw `response_text` for these 100 cases. The audit is saved as:

`analysis_outputs/deep_behavior/empty_extraction_audit.csv`

The main finding is that most empty extractions are not true "no code" responses.

| Audit check | Share of empty-extraction cases |
|---|---:|
| raw response has code indicators | 97% |
| raw response is syntactically valid Python | 94% |
| raw response defines the expected function name | 94% |

This means that the `extraction_failed` variable should be interpreted carefully. In many Llama cases, the model produced plain Python code without a markdown fence, but the extraction pipeline did not capture it. Therefore, `extraction_failed` is partly an evaluator/extractor compatibility issue, not only a model-output failure.

The 3 Qwen empty-extraction cases appear to be genuine non-code responses: the model returned explanatory reasoning without executable Python code.

This strengthens one caveat:

> Parsing/extraction failure should be treated as a pipeline-level compliance metric. It measures whether the model output was accepted by the evaluator's extraction rules, not whether the raw response always lacked valid code.

## Interpretation

The strongest interpretation is:

> Tone affects downstream coding performance mostly by changing output behavior. Neutral prompts lead to shorter, faster, more code-only responses, which fit the evaluator better. Polite and aggressive prompts encourage longer explanatory responses, which increase latency and reduce code-only compliance; these behavioral shifts explain much of the observed performance gap.

This is stronger than simply saying:

> Neutral prompts are better.

because it explains the mechanism.

## Caveats

- Behavior controls are post-treatment variables. They help explain the mechanism, but they should not be interpreted as fully causal controls.
- Completion tokens and runtime are highly correlated, so their individual coefficients are unstable when included together.
- `extraction_failed` captures empty extracted code. It is a conservative proxy for parsing failure, not a complete parser-failure taxonomy.
- The exact pass rate is low, so `tests_fraction` remains the more informative performance metric.
- The tone effect is not equally strong across all models; Llama is the main exception.

## Recommended Paper Framing

Frame the paper as:

> a controlled study of how prompt tone changes output behavior, compliance, latency, verbosity, and downstream task performance.

Do not frame it as:

> testing many prompts on many models.

The current data already supports a strong paper-style claim:

> In this coding benchmark, neutral prompts perform best overall, but the advantage is largely explained by behavioral compliance: shorter outputs, lower latency, and substantially higher code-only response rates.
