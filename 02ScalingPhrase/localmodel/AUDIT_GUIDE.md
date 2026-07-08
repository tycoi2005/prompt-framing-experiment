# Local Model Workflow And Audit Guide

This guide explains the local-model scaling study in this directory so another person or agent can reproduce the analysis, understand the dataset, and audit the claims before using them in thesis writing.

## 1. What This Directory Contains

The active study lives in:

- `results/`: current model result JSONL files.
- `problems/`: runnable problem CSVs, prompt templates, task metadata, and source problem files.
- `analyze_results.py`: main analysis script that reads `results/*.jsonl`, joins prompt metadata, computes summary CSVs, writes charts, and writes `results/analysis/report.md`.
- `results/analysis/`: generated analysis artifacts, report, SVG charts, and exploratory notebooks.
- `results_old/`: older runs and intermediate datasets. Treat these as historical context unless a comparison explicitly uses them.

The current active dataset is the set of JSONL files directly under `results/`, not `results_old/`.

## 2. Current Dataset Shape

The active result set contains six local Ollama models, two task kinds, 50 base tasks per kind, and 18 prompt variants per task:

```text
6 models x 2 task kinds x 50 tasks x 18 prompt variants = 10,800 attempts
```

Task kinds:

- `code`: Python function-generation tasks evaluated by tests.
- `math`: single-answer math tasks evaluated against expected answers.

The runnable problem files for the current local-model runs are:

- `problems/problems.csv` for code tasks.
- `problems/problem.math.csv` for math tasks.

Those runnable CSVs were generated as Cartesian products of source problems and prompt templates:

- code: `problems/VNSchoolMathProblems_lite.v0.7.json` x `problems/prompt_matrix_prompt_template.09.csv` -> `problems/problems.csv`
- math: `problems/VietJack_OnVao10_2026.math.v5.json` x `problems/prompt_matrix_prompt_template.09.math.csv` -> `problems/problem.math.csv`

In other words, the source JSON files provide the base problems, and the prompt template CSVs provide the 18 framing variants applied to each base problem.

Models:

- `nemotron-3-nano-4b_1_50`
- `gemma2-9b_1_50`
- `llama3.1-8b_1_50`
- `qwen2.5-7b_1_50`
- `mistral-7b-instruct_1_50`
- `deepseek-coder-6.7b-instruct_1_50`

Prompt factors:

- `tone`: `neutral`, `polite`, `aggressive`
- `role_binary`: `no role`, `role`
- `format`: `plaintext`, `json`, `xml`

The script infers the prompt variant from the suffix of `task_id`. For example, `17_4` means base task `17`, variant `4`.

## 3. Raw Result Format

Each result file is JSONL. Each line is one model attempt on one prompt variant.

Common fields:

- `timestamp`: when the attempt ran.
- `model`: Ollama model tag.
- `task_id`: base task plus prompt variant suffix.
- `passed`: boolean pass/fail.
- `tests_passed`, `tests_total`: code-test outcome fields.
- `errors`: evaluation or extraction errors.
- `duration_seconds`: wall-clock request/evaluation duration.
- `prompt_tokens`: prompt token count.
- `completion_tokens`: completion token count.
- `response_text`: raw model answer.
- `extracted_code`: code extracted from the response for code tasks.

Math result files use the same naming convention with `.math.jsonl`.

## 4. Prompt Metadata Join

Prompt metadata is joined from:

- `problems/prompt_matrix_prompt_template.09.csv` for code tasks.
- `problems/prompt_matrix_prompt_template.09.math.csv` for math tasks.

These are the same template files used to create the runnable problem CSVs:

- `problems/problems.csv` was created from `problems/VNSchoolMathProblems_lite.v0.7.json` x `problems/prompt_matrix_prompt_template.09.csv`.
- `problems/problem.math.csv` was created from `problems/VietJack_OnVao10_2026.math.v5.json` x `problems/prompt_matrix_prompt_template.09.math.csv`.

Important columns:

- `ID`: prompt variant id.
- `Tone`
- `Role framing`
- `Format`
- `ProblemID`
- `Prompt`
- `FinalPrompt`

`analyze_results.py` normalizes these into analysis fields:

- `variant_id`
- `base_task_id`
- `kind`
- `tone`
- `role_binary`
- `format`
- `model_slug`

Audit point: if the template CSV changes, rerun `analyze_results.py` and confirm every result row still joins to the intended prompt variant.

## 5. How To Reproduce The Analysis

From the repository root:

```bash
python 02ScalingPhrase/localmodel/analyze_results.py
```

This regenerates the main CSV artifacts, SVG charts, and Markdown report under:

```text
02ScalingPhrase/localmodel/results/analysis/
```

To execute the notebooks:

```bash
jupyter nbconvert --to notebook --execute 02ScalingPhrase/localmodel/results/analysis/important_insights_analysis.ipynb --output important_insights_analysis.executed.ipynb --output-dir 02ScalingPhrase/localmodel/results/analysis
jupyter nbconvert --to notebook --execute 02ScalingPhrase/localmodel/results/analysis/without_nemotron_analysis.ipynb --output without_nemotron_analysis.executed.ipynb --output-dir 02ScalingPhrase/localmodel/results/analysis
```

The `.ipynb` files are editable source notebooks. The `.executed.ipynb` files are rendered snapshots with outputs.

## 6. Main Generated Artifacts

Core summaries:

- `summary_by_kind.csv`: overall code versus math.
- `summary_by_model.csv`: pooled model ranking.
- `summary_by_model_and_kind.csv`: model ranking separately for code and math.
- `summary_by_variant.csv`: prompt variant performance by task kind.
- `summary_by_model_variant.csv`: prompt variant performance by model and task kind.

Prompt-factor analyses:

- `prompt_factor_summary.csv`: raw summaries for each factor level.
- `prompt_factor_contrasts.csv`: factor-level deltas versus baseline, including pass rate, score, tokens, and duration.
- `paired_fixed_effect_contrasts.csv`: paired contrasts controlling by model, kind, and base task where possible.
- `prompt_factor_interactions.csv`: two-factor interaction summaries.
- `prompt_factor_heterogeneity.csv`: how much factor effects vary across models.
- `model_factor_winners.csv`: best factor level per model/kind/factor.
- `model_kind_factor_differences.csv`: whether each factor behaves differently on math versus code, including pass-rate, token, and duration deltas.

Behavior and error analyses:

- `behavior_summary.csv`: pass rate, score, code-only behavior fields, prompt tokens, completion tokens, and duration.
- `error_category_summary.csv`: grouped failure categories.
- `token_outcome_correlations.csv`: correlations between token/duration metrics and outcomes.

Dataset sensitivity:

- `dataset_shift_summary.csv`: comparison with the earlier pilot code-only dataset and comparable scaled subsets.
- `without_nemotron_analysis.ipynb`: sensitivity analysis excluding Nemotron.

Model-size context:

- `model_size_comparison.csv`: model parameter count and local Ollama manifest size in GiB.

Reports and notebooks:

- `report.md`: main text report generated by `analyze_results.py`.
- `important_insights_analysis.ipynb`: visual notebook for thesis-relevant insights.
- `important_insights_analysis.executed.ipynb`: executed version of the visual notebook.
- `without_nemotron_analysis.ipynb`: visual notebook excluding Nemotron.
- `without_nemotron_analysis.executed.ipynb`: executed version of the no-Nemotron notebook.

## 7. Audit Checklist

### Data Completeness

Check that every active model has both code and math files:

```bash
ls 02ScalingPhrase/localmodel/results/*.jsonl
```

Expected active files:

- six `*.jsonl` code files
- six `*.math.jsonl` math files

Check row count after analysis:

```bash
python - <<'PY'
import csv
from pathlib import Path
p = Path('02ScalingPhrase/localmodel/results/analysis/summary_by_kind.csv')
with p.open() as f:
    print(list(csv.DictReader(f)))
PY
```

The total `n` across code and math should be `10800`.

### Join Integrity

Audit whether task ids map cleanly to prompt variants:

- variant id should be `1` through `18`.
- every row should have non-empty `tone`, `role_binary`, and `format`.
- code rows should join to the code template CSV.
- math rows should join to the math template CSV.

If a prompt-template CSV is regenerated, compare the old and new `ID`, `Tone`, `Role framing`, and `Format` columns before rerunning thesis analyses.

### Model And Task Balance

Check `summary_by_model_and_kind.csv`:

- each model/kind group should have `n = 900`.
- each model has `50 tasks x 18 variants = 900` attempts for code and `900` attempts for math.
- each model should therefore have `1800` total attempts.

Do not compare pooled model averages without also reporting model-by-kind results, because math and code difficulty differ strongly.

### Prompt Factor Claims

For any thesis claim about tone, role framing, or format, inspect all three levels of evidence:

1. `prompt_factor_contrasts.csv`: raw difference from baseline.
2. `paired_fixed_effect_contrasts.csv`: paired contrast controlling for model, kind, and base task.
3. `prompt_factor_heterogeneity.csv` and `model_kind_factor_differences.csv`: whether the effect changes by model or task kind.

Recommended wording:

- Use "associated with" or "in this dataset" unless the paired analysis and heterogeneity checks support a stronger claim.
- Avoid saying a prompt factor "works" globally if it helps one model/kind and hurts another.

### Model-Dominance Sensitivity

Nemotron is much stronger than the other models on math in this run. This can change pooled averages substantially.

Before making a thesis-level claim:

- compare full-dataset charts with `without_nemotron_analysis.ipynb`;
- check whether the claim still holds without Nemotron;
- state clearly if a finding is driven mainly by Nemotron.

### Task-Kind Sensitivity

Math and code behave differently. For example, a format that reduces math pass rate may have little or positive effect on code.

Before claiming a prompt effect:

- check code separately;
- check math separately;
- check `model_kind_factor_differences.csv` for math-minus-code differences.

### Duration And Token Audit

Do not report only pass rate. Also audit:

- `prompt_tokens`
- `completion_tokens`
- `duration_seconds`

Relevant files:

- `prompt_factor_contrasts.csv`
- `behavior_summary.csv`
- `model_kind_factor_differences.csv`
- `token_outcome_correlations.csv`

Important interpretation rule: lower token count or shorter duration is not automatically better if pass rate drops. For example, a concise format may reduce completion tokens while also reducing accuracy.

### Error-Mode Audit

For code tasks, inspect:

- `invalid_python`
- `name_not_defined`
- `missing_or_empty_code`
- `timeout`
- `wrong_answer`

For math tasks, most failures are answer correctness failures rather than code-execution errors.

Use `error_category_summary.csv` before claiming why a prompt failed. A lower pass rate can come from extraction problems, invalid code, runtime errors, or wrong reasoning.

### Model-Size Audit

`model_size_comparison.csv` reports local Ollama manifest size in GiB, not full-precision memory footprint.

Use model size only as context. Do not imply that parameter count or GiB size alone explains performance.

Audit point: if local Ollama models are pulled or updated again, regenerate or re-check `model_size_comparison.csv` from local manifests.

## 8. Known Interpretation Traps

Pooling can mislead:

- Adding weaker models changes overall averages even if the prompt templates did not change.
- Adding math changes conclusions because math has a different baseline pass rate and error profile than code.
- A prompt effect can reverse across task kinds or models.

Prompt variants are not independent in the same way as separate tasks:

- the same base problem appears under 18 prompt variants;
- paired comparisons by base task are more defensible than raw pooled differences;
- report raw and paired results together.

Pass rate is not the whole behavior:

- a prompt can improve pass rate while increasing duration or completion tokens;
- a prompt can reduce tokens by causing shorter but less correct answers;
- token and duration findings should be interpreted jointly with accuracy.

## 9. Recommended Thesis Claim Standard

Before writing a thesis-level claim, require these checks:

1. The result appears in both the report and the visual notebook.
2. The relevant CSV row has enough `n` to be meaningful.
3. The effect is checked separately for code and math.
4. The effect is checked across models or with model-specific contrasts.
5. The no-Nemotron sensitivity notebook does not contradict the claim, or the claim explicitly says Nemotron drives it.
6. Token count and duration are reported if the claim is about efficiency, verbosity, or behavior.
7. Error categories are checked if the claim explains failure causes.

## 10. Quick Audit Commands

Regenerate analysis:

```bash
python 02ScalingPhrase/localmodel/analyze_results.py
```

List generated artifacts:

```bash
ls -la 02ScalingPhrase/localmodel/results/analysis
```

Check active result files:

```bash
ls 02ScalingPhrase/localmodel/results/*.jsonl
```

Inspect the main report:

```bash
sed -n '1,140p' 02ScalingPhrase/localmodel/results/analysis/report.md
```

Check for notebook execution errors:

```bash
python - <<'PY'
import json
from pathlib import Path
for path in [
    Path('02ScalingPhrase/localmodel/results/analysis/important_insights_analysis.executed.ipynb'),
    Path('02ScalingPhrase/localmodel/results/analysis/without_nemotron_analysis.executed.ipynb'),
]:
    nb = json.loads(path.read_text())
    errors = []
    for i, cell in enumerate(nb.get('cells', [])):
        for out in cell.get('outputs', []):
            if out.get('output_type') == 'error':
                errors.append((i, out.get('ename'), out.get('evalue')))
    print(path.name, 'errors=', len(errors), errors[:3])
PY
```

## 11. What To Hand To A Reviewer

For a compact audit package, point reviewers to:

- `AUDIT_GUIDE.md`
- `analyze_results.py`
- `results/`
- `problems/problems.csv`
- `problems/problem.math.csv`
- `problems/VNSchoolMathProblems_lite.v0.7.json`
- `problems/VietJack_OnVao10_2026.math.v5.json`
- `problems/prompt_matrix_prompt_template.09.csv`
- `problems/prompt_matrix_prompt_template.09.math.csv`
- `results/analysis/report.md`
- `results/analysis/important_insights_analysis.executed.ipynb`
- `results/analysis/without_nemotron_analysis.executed.ipynb`
- `results/analysis/model_size_comparison.csv`

That package is enough to understand the workflow, reproduce the summaries, and evaluate whether the thesis claims are supported by the data.
