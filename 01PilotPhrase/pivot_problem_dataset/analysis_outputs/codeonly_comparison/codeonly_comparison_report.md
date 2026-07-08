# Code-Only System Prompt Comparison

System prompt tested:

> Output only the code, no explanations.

Baseline: corrected fixed-extractor results (`results/*_fixextractor.jsonl`).
Code-only condition: `results_codeonly/*.jsonl`.

## Overall Result

| Condition | Passes | Pass rate | Avg. tests passed | Avg. completion tokens | Avg. duration | Code-only rate |
|---|---:|---:|---:|---:|---:|---:|
| baseline_fixed | 254/2700 | 9.4% | 13.3% | 605 | 18.16s | 25.2% |
| codeonly_system | 277/2700 | 10.3% | 15.7% | 290 | 9.00s | 99.5% |

Overall, the code-only system prompt changed exact passes from 254/2700 to 277/2700, a pass-rate change of +0.9 pp. It changed average tests passed by +2.4 pp, completion length by -316 tokens, and code-only rate by +74.3 pp.

## By Model

| Model | Baseline passes | Code-only passes | Pass-rate delta | Tests-fraction delta | Token delta | Code-only-rate delta |
|---|---:|---:|---:|---:|---:|---:|
| gemma2-9b | 85/900 (9.4%) | 100/900 (11.1%) | +1.7 pp | +4.8 pp | -422 | +72.6 pp |
| llama3.1-8b | 48/900 (5.3%) | 56/900 (6.2%) | +0.9 pp | +2.1 pp | -173 | +77.0 pp |
| qwen2.5-7b | 121/900 (13.4%) | 121/900 (13.4%) | +0.0 pp | +0.3 pp | -352 | +73.3 pp |


## Interpretation

The system prompt improves measured exact pass rate overall, but the effect is model-specific. It helps Gemma and Llama, while Qwen's exact pass count is unchanged. The comparison should be interpreted as a controlled prompt-policy intervention: adding a global code-only instruction changes output behavior and modestly changes downstream performance.

The key research implication is that explicit output constraints can reduce evaluator-compliance problems, but they do not remove prompt-factor effects entirely. Under the code-only system prompt, tone still affects performance: neutral remains best overall by tests fraction, while polite/aggressive improve more than neutral because they had the largest verbosity/compliance problem in the baseline. Role framing remains small, and format effects remain modest/model-dependent.
