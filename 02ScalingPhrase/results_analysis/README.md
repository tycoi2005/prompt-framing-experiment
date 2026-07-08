# Results Analysis Dataset Inventory

This folder is a compact handoff package for the prompt-scaling analyses. It copies the final result files, runnable problem files, source problem files, and prompt templates from both the local-model study and the API-model study.

It is intended for audit, sharing, and downstream analysis. The original source locations remain:

- local/small models: `02ScalingPhrase/localmodel`
- API models: `02ScalingPhrase/apimodel/run_apis`

## Verification Status

Verified on May 14, 2026:

- `26` copied files were compared against their source files.
- `26 / 26` matched exactly.
- No copied file was missing.
- No copied file differed from its source.

Result-file integrity checks:

| Group | Files | Rows per result file | Duplicate task keys | Bad JSON lines | Empty responses |
|---|---:|---:|---:|---:|---:|
| `smallmodels` | 12 | 900 each | 0 | 0 | 14 total |
| `apimodels` | 4 | 900 each | 0 | 0 | 0 |

Prompt/problem version checks:

- The copied prompt-template files match the active source templates exactly.
- The copied runnable problem matrices match the active source problem matrices exactly.
- Each runnable problem matrix has `900` rows: `50` base tasks x `18` prompt variants.
- The code and math prompt templates each have exactly `18` rows with IDs `1-18`.
- Every result JSONL file covers exactly the same `900` task/category keys as its corresponding runnable problem matrix.
- No result file has task/category keys outside its corresponding problem matrix.
- No result file is missing task/category keys from its corresponding problem matrix.

Conclusion: the copied prompt templates and problem matrices are the active versions used by the current final result files in this package.

The only remaining empty responses are in:

- `smallmodels/nemotron-3-nano-4b_1_50.jsonl`: 14 empty code responses.

Those are known unresolved Nemotron code empty-generation failures retained to keep the dataset at 900 rows for that model/kind.

## Folder Layout

```text
results_analysis/
  apimodels/
    *.jsonl
    problems/
  prompt_templates/
  smallmodels/
    *.jsonl
    problems/
```

## Prompt Templates

These templates define the 18 prompt framing variants used across the studies.

### `prompt_templates/prompt_matrix_prompt_template.09.csv`

Code/Python prompt-template matrix.

Source:

```text
02ScalingPhrase/localmodel/problems/prompt_matrix_prompt_template.09.csv
```

Purpose:

- Defines prompt variant `ID` values for code tasks.
- Encodes `Tone`, `Role framing`, and `Format`.
- Used to generate local-model `smallmodels/problems/problems.csv`.
- Also used as prompt metadata for API Python analyses.

### `prompt_templates/prompt_matrix_prompt_template.09.math.csv`

Math prompt-template matrix.

Source:

```text
02ScalingPhrase/localmodel/problems/prompt_matrix_prompt_template.09.math.csv
```

Purpose:

- Defines prompt variant `ID` values for math tasks.
- Encodes `Tone`, `Role framing`, and `Format`.
- Used to generate local-model `smallmodels/problems/problem.math.csv`.
- Also used as prompt metadata for API math analyses.

## Smallmodels

`smallmodels/` contains the final local Ollama model result JSONL files.

Each result file has:

- `900` rows
- `50` base tasks
- `18` prompt variants per task
- one row per model attempt

Filename convention:

- `*.jsonl`: code/Python task results
- `*.math.jsonl`: math task results

Common fields include:

- `timestamp`
- `model`
- `task_id`
- `passed`
- `duration_seconds`
- `prompt_tokens`
- `completion_tokens`
- `response_text`
- `errors`

Code files also include fields such as:

- `tests_passed`
- `tests_total`
- `extracted_code`

Math files also include fields such as:

- `expected_answer`
- `extracted_values`
- `values_passed`
- `values_total`

### Smallmodel Result Files

| File | Model | Kind | Rows | Passed | Empty responses | Notes |
|---|---|---|---:|---:|---:|---|
| `smallmodels/deepseek-coder-6.7b-instruct_1_50.jsonl` | DeepSeek Coder 6.7B Instruct | code | 900 | 10 | 0 | Local Ollama code run. |
| `smallmodels/deepseek-coder-6.7b-instruct_1_50.math.jsonl` | DeepSeek Coder 6.7B Instruct | math | 900 | 51 | 0 | Local Ollama math run. |
| `smallmodels/gemma2-9b_1_50.jsonl` | Gemma 2 9B | code | 900 | 102 | 0 | Local Ollama code run. |
| `smallmodels/gemma2-9b_1_50.math.jsonl` | Gemma 2 9B | math | 900 | 137 | 0 | Local Ollama math run. |
| `smallmodels/llama3.1-8b_1_50.jsonl` | Llama 3.1 8B | code | 900 | 52 | 0 | Local Ollama code run. |
| `smallmodels/llama3.1-8b_1_50.math.jsonl` | Llama 3.1 8B | math | 900 | 389 | 0 | Local Ollama math run. |
| `smallmodels/mistral-7b-instruct_1_50.jsonl` | Mistral 7B Instruct | code | 900 | 4 | 0 | Local Ollama code run. |
| `smallmodels/mistral-7b-instruct_1_50.math.jsonl` | Mistral 7B Instruct | math | 900 | 69 | 0 | Local Ollama math run. |
| `smallmodels/nemotron-3-nano-4b_1_50.jsonl` | Nemotron 3 Nano 4B | code | 900 | 205 | 14 | Merged with rerun file; 14 unresolved empty responses remain. |
| `smallmodels/nemotron-3-nano-4b_1_50.math.jsonl` | Nemotron 3 Nano 4B | math | 900 | 821 | 0 | Rerun repaired previous empty math responses. |
| `smallmodels/qwen2.5-7b_1_50.jsonl` | Qwen 2.5 7B | code | 900 | 119 | 0 | Local Ollama code run. |
| `smallmodels/qwen2.5-7b_1_50.math.jsonl` | Qwen 2.5 7B | math | 900 | 212 | 0 | Local Ollama math run. |

### `smallmodels/problems/problems.csv`

Runnable local-model code problem matrix.

Source:

```text
02ScalingPhrase/localmodel/problems/problems.csv
```

Created from:

```text
VNSchoolMathProblems_lite.v0.7.json x prompt_matrix_prompt_template.09.csv
```

Purpose:

- Contains code/Python prompts after applying the 18 prompt-template variants to each base problem.
- Used by local Ollama code runs.

### `smallmodels/problems/problem.math.csv`

Runnable local-model math problem matrix.

Source:

```text
02ScalingPhrase/localmodel/problems/problem.math.csv
```

Created from:

```text
VietJack_OnVao10_2026.math.v5.json x prompt_matrix_prompt_template.09.math.csv
```

Purpose:

- Contains math prompts after applying the 18 prompt-template variants to each base problem.
- Used by local Ollama math runs.

### `smallmodels/problems/VNSchoolMathProblems_lite.v0.7.json`

Source base-problem JSON for the local-model code tasks.

Source:

```text
02ScalingPhrase/localmodel/problems/VNSchoolMathProblems_lite.v0.7.json
```

Purpose:

- Provides the base problem definitions before prompt-template expansion.
- Used to generate `smallmodels/problems/problems.csv`.

### `smallmodels/problems/VietJack_OnVao10_2026.math.v5.json`

Source base-problem JSON for the local-model math tasks.

Source:

```text
02ScalingPhrase/localmodel/problems/VietJack_OnVao10_2026.math.v5.json
```

Purpose:

- Provides the base math problem definitions before prompt-template expansion.
- Used to generate `smallmodels/problems/problem.math.csv`.

## Apimodels

`apimodels/` contains the final API-model benchmark result JSONL files.

Each result file has:

- `900` rows
- `50` base tasks
- `18` prompt variants per task
- one row per API model attempt

Filename convention:

- `*.python.jsonl`: API Python/code task results
- `*.math.jsonl`: API math task results

Common fields include:

- `task_id`
- `category_id`
- `row_key`
- `model`
- `passed`
- `duration_seconds`
- `response_text`
- `raw_usage`
- `error`
- `eval_result`

### API Result Files

| File | Model | Kind | Rows | Passed | Empty responses | Notes |
|---|---|---|---:|---:|---:|---|
| `apimodels/deepseek-v4-flash.math.jsonl` | DeepSeek V4 Flash | math | 900 | 742 | 0 | Final API math result. |
| `apimodels/deepseek-v4-flash.python.jsonl` | DeepSeek V4 Flash | python | 900 | 600 | 0 | Final API Python result. |
| `apimodels/gemini-flash.math.jsonl` | Gemini Flash | math | 900 | 217 | 0 | Final API math result. |
| `apimodels/gemini-flash.python.jsonl` | Gemini Flash | python | 900 | 621 | 0 | Final API Python result. |

### `apimodels/problems/problems.csv`

Runnable API Python/code problem matrix.

Source:

```text
02ScalingPhrase/apimodel/run_apis/problems.csv
```

Purpose:

- Contains Python/code prompts for the API benchmark.
- Uses the shared 18 prompt-template framing setup.
- Used by `run_api_matrix.py` for API Python runs.

### `apimodels/problems/problems.math.csv`

Runnable API math problem matrix.

Source:

```text
02ScalingPhrase/apimodel/run_apis/problems.math.csv
```

Purpose:

- Contains math prompts for the API benchmark.
- Uses the shared 18 prompt-template framing setup.
- Used by `run_api_matrix.py` for API math runs.

### `apimodels/problems/base-mathproblems.bigmodel.v7.python.json`

Source base-problem JSON for API Python/code tasks.

Source:

```text
02ScalingPhrase/apimodel/base-mathproblems.bigmodel.v7.python.json
```

Purpose:

- Provides the base Python/code task definitions before expansion into API runnable prompts.
- Corresponds to the v7 Python API benchmark problem set.

### `apimodels/problems/base-mathproblems.bigmodel.v5.csv`

Source/base math problem table for API math tasks.

Source:

```text
02ScalingPhrase/apimodel/crafting_math_problems/base-mathproblems.bigmodel.v5.csv
```

Purpose:

- Provides the base math task set used to create the API math prompt matrix.
- Corresponds to the v5 math API benchmark problem set.

## How To Use This Package

For audit:

1. Confirm each result file has `900` rows.
2. Confirm no duplicate task keys exist inside each result file.
3. Confirm prompt variant IDs cover `1-18`.
4. Join result rows to prompt metadata through `category_id` or the prompt variant suffix.
5. Analyze math and code/Python separately before making pooled claims.
6. Treat the 14 remaining Nemotron code empty responses as known unresolved generation failures.

For analysis:

- Use `smallmodels/` when comparing local Ollama models.
- Use `apimodels/` when comparing API models.
- Use `prompt_templates/` to recover tone, role framing, and format for each prompt variant.
- Use each `problems/` subfolder to trace from result rows back to runnable prompts and base problems.

## Provenance Summary

| Copied file group | Original source directory |
|---|---|
| `smallmodels/*.jsonl` | `02ScalingPhrase/localmodel/results/` |
| `smallmodels/problems/*` | `02ScalingPhrase/localmodel/problems/` |
| `prompt_templates/*` | `02ScalingPhrase/localmodel/problems/` |
| `apimodels/*.jsonl` | `02ScalingPhrase/apimodel/run_apis/results_final/` |
| `apimodels/problems/problems.csv` | `02ScalingPhrase/apimodel/run_apis/problems.csv` |
| `apimodels/problems/problems.math.csv` | `02ScalingPhrase/apimodel/run_apis/problems.math.csv` |
| `apimodels/problems/base-mathproblems.bigmodel.v7.python.json` | `02ScalingPhrase/apimodel/base-mathproblems.bigmodel.v7.python.json` |
| `apimodels/problems/base-mathproblems.bigmodel.v5.csv` | `02ScalingPhrase/apimodel/crafting_math_problems/base-mathproblems.bigmodel.v5.csv` |
