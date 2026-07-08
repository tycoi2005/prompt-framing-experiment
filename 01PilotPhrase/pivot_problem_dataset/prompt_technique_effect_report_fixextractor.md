# Fixed-Extractor Prompt Technique Effects Report

Based on `fixed_extractor_analysis.executed.ipynb` and the corrected `*_fixextractor.jsonl` result files.

## Executive Summary

After fixing the code extractor, the overall conclusion remains the same but is cleaner: **tone affects both model behavior and performance**. Neutral prompts still perform best overall, but the deeper behavior-control analysis shows that the apparent neutral-tone advantage is largely explained by output behavior: shorter outputs, faster runtime, and much higher code-only compliance.

The extractor fix mainly affected `llama3.1-8b`: its exact pass count increased from 35/900 to 48/900 because many plain Python responses had previously been missed by the markdown-fence-only extractor.

## Data Analyzed

- Result files: `results/gemma2-9b_fixextractor.jsonl`, `results/llama3.1-8b_fixextractor.jsonl`, `results/qwen2.5-7b_fixextractor.jsonl`
- Models: 3
- Problems: 50
- Prompt templates: 18
- Total runs: 2,700
- Prompt factors analyzed: `Tone`, `Role_framing`, `Format`
- Output directory: `analysis_outputs/fixed_extractor/`

## Extractor Fix Impact

| Model | Original passes | Fixed passes | Changed extractions | Changed pass/fail |
|---|---:|---:|---:|---:|
| gemma2-9b | 85/900 | 85/900 | 0 | 0 |
| llama3.1-8b | 35/900 | 48/900 | 97 | 13 |
| qwen2.5-7b | 121/900 | 121/900 | 3 | 0 |


The fix confirms that the original extraction failure variable should be interpreted as a pipeline compatibility issue, not always a true model failure. The fixed evaluator now treats unfenced plain Python as candidate code and rejects non-Python responses with `Response is not valid Python`.

## Corrected Model Performance

| Model | Runs | Pass rate | Avg. tests passed | Avg. duration | Avg. completion tokens | Code-only rate |
|---|---:|---:|---:|---:|---:|---:|
| qwen2.5-7b | 900 | 13.4% | 17.0% | 18.59s | 653 | 26.7% |
| gemma2-9b | 900 | 9.4% | 14.0% | 19.56s | 601 | 25.9% |
| llama3.1-8b | 900 | 5.3% | 8.9% | 16.33s | 562 | 23.0% |


## Main Finding: Neutral Tone Still Performs Best Overall

| Tone | Runs | Pass rate | Avg. tests passed | Avg. completion tokens | Avg. duration | Code-only rate |
|---|---:|---:|---:|---:|---:|---:|
| neutral | 900 | 11.8% | 16.9% | 413 | 12.62s | 69.4% |
| polite | 900 | 8.1% | 11.3% | 716 | 21.47s | 1.6% |
| aggressive | 900 | 8.3% | 11.7% | 687 | 20.40s | 4.6% |

Paired comparisons versus neutral show:

| Comparison | Pass-rate delta | Tests-fraction delta | Completion-token delta | Code-only-rate delta |
|---|---:|---:|---:|---:|
| polite vs neutral | -3.7 pp | -5.6 pp | +304 | -67.9 pp |
| aggressive vs neutral | -3.4 pp | -5.3 pp | +274 | -64.9 pp |

## Deep Behavior-Control Result

With aggressive tone as the regression reference category, the baseline fixed-effect model estimates neutral tone as:

- pass/fail: +3.4 pp, p = 0.0050
- tests fraction: +5.3 pp, p = 0.0001

After adding behavior controls, the neutral-tone coefficient becomes non-significant:

| Outcome | Model | Neutral coefficient | p-value |
|---|---|---:|---:|
| pass/fail | prompt only | +3.4 pp | 0.0050 |
| pass/fail | + output length | -2.7 pp | 0.0859 |
| pass/fail | + code-only | +0.8 pp | 0.5996 |
| pass/fail | + runtime | -2.2 pp | 0.1434 |
| pass/fail | all behavior controls | -2.8 pp | 0.0877 |
| tests fraction | prompt only | +5.3 pp | 0.0001 |
| tests fraction | + output length | -1.9 pp | 0.2710 |
| tests fraction | + code-only | +1.5 pp | 0.3980 |
| tests fraction | + runtime | -1.5 pp | 0.3843 |
| tests fraction | all behavior controls | -2.5 pp | 0.1882 |

This supports the mediation-style interpretation: **neutral prompts perform better largely because they produce shorter, cleaner, more code-focused outputs.**

## Model-Specific Caveat

Neutral tone is strongest overall, but the effect is not identical across models. After fixing extraction, Llama improves, but the overall tone mechanism still differs by model family. The paper should avoid claiming that neutral tone universally improves every model in every setting.

## Interpretation

The strongest updated interpretation is:

> Prompt tone affects downstream coding performance mostly by changing output behavior. Neutral prompts lead to shorter, faster, more code-only responses, which fit the evaluator better. Polite and aggressive prompts encourage longer explanatory responses, which increases latency and reduces code-only compliance; these behavioral shifts explain much of the observed performance gap.

## Caveats

- Behavior controls are post-treatment variables, so they explain mechanism but should not be interpreted as fully causal controls.
- Completion tokens and runtime are highly correlated, so their individual coefficients should be interpreted carefully when included together.
- The fixed extractor reduces false `No code extracted` failures, but future experiments should use the fixed extractor from the start.
- Exact pass rates remain low, so `tests_fraction` is still the more informative performance metric.

## Recommended Paper Framing

Frame the paper as:

> a controlled study of how prompt tone changes output behavior, compliance, latency, verbosity, and downstream task performance.

The corrected data strengthens the paper because it removes a known evaluator artifact while preserving the main behavioral explanation.
