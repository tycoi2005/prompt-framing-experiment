# Pivot experiment report

## Executive Summary

The clearest finding is that **tone affects both model behavior and performance**. Neutral prompts performed best overall, while polite and aggressive tones produced longer, slower, more explanatory outputs and lower average test performance.

`Role_framing` and `Format` had much smaller effects. The evidence does not strongly support that adding a developer role improves correctness. Plaintext was slightly better than JSON/XML on average, but format effects were modest and less consistent across models.

## Data Analyzed

- Result files: `results/gemma2-9b_final.jsonl`, `results/llama3.1-8b_final.jsonl`, `results/qwen2.5-7b_final.jsonl`
- Models: 3
- Problems: 50
- Prompt templates: 18
- Total runs: 2,700
- Prompt factors analyzed: `Tone`, `Role_framing`, `Format`
- `Pressure` was not analyzed because it was empty/constant in the prompt matrix.

## Overall Model Performance

| Model | Runs | Pass rate | Avg. tests passed | Avg. duration | Avg. completion tokens | Code-only rate |
|---|---:|---:|---:|---:|---:|---:|
| qwen2.5-7b | 900 | 13.4% | 17.0% | 18.59s | 653 | 26.3% |
| gemma2-9b | 900 | 9.4% | 14.0% | 19.56s | 601 | 25.9% |
| llama3.1-8b | 900 | 3.9% | 6.4% | 16.33s | 562 | 12.2% |

The absolute pass rates are low, so the more sensitive metric is often `tests_fraction`, the fraction of unit tests passed. Exact pass/fail is still useful, but it loses information when many outputs fail at least one test.

## Main Finding: Neutral Tone Performs Best

Across all models and templates, neutral prompts had the strongest performance.

| Tone | Runs | Pass rate | Avg. tests passed | Avg. duration | Avg. completion tokens | Code-only rate |
|---|---:|---:|---:|---:|---:|---:|
| neutral | 900 | 10.9% | 15.4% | 12.62s | 413 | 62.3% |
| polite | 900 | 8.0% | 11.2% | 21.47s | 716 | 1.4% |
| aggressive | 900 | 7.9% | 10.8% | 20.40s | 687 | 0.7% |

The paired comparison, which compares prompt levels within the same `(model, problem)` pairs, shows:

| Comparison | Pass-rate delta | Tests-fraction delta |
|---|---:|---:|
| polite vs neutral | -2.9 percentage points | -4.2 percentage points |
| aggressive vs neutral | -3.0 percentage points | -4.6 percentage points |

The fixed-effect regression supports the same conclusion. With aggressive tone as the hidden reference category, neutral tone was associated with:

- `+3.0` percentage points on exact pass rate (`p = 0.0123`)
- `+4.6` percentage points on tests passed fraction (`p = 0.0003`)

Polite tone was not meaningfully different from aggressive tone on correctness in the regression.

## Tone Also Changes Behavior

Tone had a much larger behavioral effect than role framing or output format.

Compared with neutral prompts, polite and aggressive prompts generated much longer outputs:

| Comparison | Completion-token delta | Duration delta | Code-only-rate delta |
|---|---:|---:|---:|
| polite vs neutral | +304 tokens | +8.85s | -60.9 percentage points |
| aggressive vs neutral | +274 tokens | +7.78s | -61.7 percentage points |

This suggests that polite/aggressive prompt variants encouraged more prose, explanation, or wrapper text. That behavior likely hurt the coding benchmark because the task expects executable code, and extra text can interfere with extraction or evaluation.

## Role Framing Has Little Evidence of Benefit

Role framing had a small effect overall.

| Role framing | Runs | Pass rate | Avg. tests passed | Avg. completion tokens | Code-only rate |
|---|---:|---:|---:|---:|---:|
| no role | 1,350 | 9.3% | 12.7% | 605 | 22.2% |
| developer role | 1,350 | 8.5% | 12.2% | 605 | 20.7% |

The paired comparison found developer role was slightly worse than no role:

- exact pass rate: `-0.8` percentage points
- tests fraction: `-0.5` percentage points

These differences are small, and the regression p-values were not statistically convincing. The practical interpretation is: **developer role framing did not clearly improve performance in this experiment**.

## Format Effects Are Modest and Model-Specific

Plaintext was slightly stronger overall than JSON/XML, but the effect was smaller than tone.

| Format | Runs | Pass rate | Avg. tests passed | Avg. completion tokens | Code-only rate |
|---|---:|---:|---:|---:|---:|
| plaintext | 900 | 9.4% | 13.3% | 603 | 21.0% |
| xml | 900 | 9.1% | 12.4% | 601 | 24.3% |
| json | 900 | 8.2% | 11.7% | 612 | 19.1% |

Paired effects versus plaintext:

| Comparison | Pass-rate delta | Tests-fraction delta |
|---|---:|---:|
| JSON vs plaintext | -1.2 percentage points | -1.6 percentage points |
| XML vs plaintext | -0.3 percentage points | -0.9 percentage points |

These are modest and their confidence intervals overlap zero. Format may still matter for individual models: for example, qwen2.5-7b did much better with plaintext than JSON/XML, while gemma2-9b showed stronger average tests fraction with XML.

## Best and Worst Prompt Templates

The best complete template was:

| Template | Tone | Role | Format | Pass rate | Avg. tests passed |
|---:|---|---|---|---:|---:|
| 1 | neutral | no role | plaintext | 13.3% | 18.4% |

Other strong templates were also mostly neutral:

| Template | Tone | Role | Format | Pass rate | Avg. tests passed |
|---:|---|---|---|---:|---:|
| 5 | neutral | developer role | json | 12.7% | 17.7% |
| 6 | neutral | developer role | xml | 12.7% | 16.1% |
| 3 | neutral | no role | xml | 11.3% | 15.2% |

The weakest templates were mostly polite or aggressive, especially with developer role or JSON/XML formatting.

## Interpretation

The main behavioral mechanism appears to be verbosity. Neutral prompts produced shorter, more code-focused answers and had the highest code-only rate. Polite and aggressive prompts produced hundreds more completion tokens on average, took longer, and were much less likely to return code-only outputs.

For this benchmark, the safest prompt technique is:

> neutral tone + simple/plaintext instructions + no unnecessary persona or role pressure

That combination best matches the evaluator’s needs: concise executable code with minimal extra prose.