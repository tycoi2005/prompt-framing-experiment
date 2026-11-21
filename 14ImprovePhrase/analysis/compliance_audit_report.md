# Compliance Metrics Audit Report (`R2C13` & `R2C21`)

## 1. Key Findings

1. **Critical Bug Caught in Original API Python Code-Only Compliance (`recompute_manuscript_tables.py` line 124):**
   - Original script read top-level `row.get('extracted_code')`, which exists for Local Code JSONLs but is **absent** in API Python JSONLs (which store `eval_result.candidate_code`).
   - As a result, original API Python `code_only` compliance was erroneously reported as **0.0%** instead of its true value computed from `strict_extract_code(response_text)`.
2. **Math Raw-Response Audit (Original 14,400 vs. New `k = 3` Full-Raw Dataset):**
   - Inspecting `completion_tokens >= 50` with `len(response_text) < 20` flags cases where either normalized answers were logged OR internal reasoning tokens were hidden from `response_text` (e.g., `nemotron-3-nano-4b` and `deepseek-v4-flash` reasoning models).
   - Our new `k = 3` dataset (`14,398` runs) saved **complete raw `response_text`** directly from Ollama/API for all 8 models, providing verified ground-truth compliance.
3. **Validation of the 15% Code-Only Rule Against Actual Strict-Parser (`strict_extract_code` + `ast.parse`) Acceptance:**
   - The 15% rule has **high precision** for parser acceptance (nearly all `<15%` extra-text outputs parse cleanly via `ast.parse`), **but lower recall**: a substantial share of outputs with `>=15%` surrounding prose still contain a valid fenced Python block that our strict parser accepts.
   - Therefore, `<15%` extra text measures **strict conciseness / zero-chatter adherence**, NOT parser survivability — both metrics must be reported and distinguished explicitly.

## 2. Math Raw-Response & Compliance Audit Table

| source | regime | model | n | mean_comp_tok | med_resp_chars | med_chars_per_tok | pct_tok>=50_and_chars<20 | pct_resp_lt50_chars | pct_single_line |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_14400 | api | deepseek-v4-flash | 900 | 1127.24 | 3.00 | 0.01 | 61.89 | 78.44 | 79.33 |
| original_14400 | api | gemini-flash | 900 | 14.77 | 2.00 | 1.00 | 0.00 | 99.44 | 100.00 |
| original_14400 | local | deepseek-coder-6.7b-instruct | 900 | 287.06 | 917.00 | 3.41 | 0.00 | 0.00 | 3.78 |
| original_14400 | local | gemma2-9b | 900 | 6.10 | 6.00 | 1.00 | 0.00 | 99.89 | 100.00 |
| original_14400 | local | llama3.1-8b | 900 | 273.57 | 511.00 | 3.07 | 0.00 | 6.56 | 14.33 |
| original_14400 | local | mistral-7b-instruct | 900 | 78.65 | 56.00 | 2.84 | 0.00 | 46.33 | 80.22 |
| original_14400 | local | nemotron-3-nano-4b | 900 | 288.63 | 3.00 | 0.02 | 97.44 | 99.78 | 99.78 |
| original_14400 | local | qwen2.5-7b | 900 | 5.56 | 3.00 | 0.75 | 0.00 | 99.78 | 99.67 |
| new_k3_raw | api | deepseek-v4-flash-aimlapi | 900 | 825.42 | 2.00 | 0.01 | 80.78 | 90.00 | 80.56 |
| new_k3_raw | api | gemini-flash | 900 | 10.15 | 2.00 | 1.00 | 0.00 | 99.67 | 100.00 |
| new_k3_raw | local | deepseek-coder-6.7b-instruct | 899 | 305.16 | 904.00 | 3.34 | 0.00 | 0.00 | 1.89 |
| new_k3_raw | local | gemma2-9b | 900 | 5.64 | 5.00 | 0.83 | 0.00 | 100.00 | 100.00 |
| new_k3_raw | local | llama3.1-8b | 900 | 250.00 | 529.00 | 3.11 | 0.00 | 8.56 | 21.11 |
| new_k3_raw | local | mistral-7b-instruct | 900 | 57.19 | 43.00 | 2.50 | 0.00 | 64.11 | 86.33 |
| new_k3_raw | local | nemotron-3-nano-4b | 900 | 292.67 | 3.00 | 0.02 | 98.22 | 100.00 | 99.89 |
| new_k3_raw | local | qwen2.5-7b | 900 | 4.60 | 3.00 | 0.75 | 0.00 | 100.00 | 100.00 |

## 3. Code-Only 15% Rule vs. Actual Strict-Parser (`ast.parse`) Validation

| dataset | regime | n | buggy_code_only_pct | fixed_code_only_15pct | strict_parser_ast_ok_pct | agreement_pct | precision_of_15pct_for_ast_ok | recall_of_15pct_for_ast_ok | fn_prose_gt15_but_parses_pct | fp_lt15_but_syntax_err_pct | pass_rate_when_15pct_true | pass_rate_when_prose_gt15_but_ast_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_14400 | api | 1800 | 0.00 | 93.39 | 93.44 | 99.94 | 100.00 | 99.94 | 0.06 | 0.00 | 72.58 | 100.00 |
| original_14400 | local | 5400 | 72.87 | 72.00 | 97.56 | 73.63 | 99.43 | 73.39 | 25.96 | 0.41 | 11.88 | 2.14 |
| new_k3_14398 | api | 1800 | NaN | 75.72 | 74.61 | 98.89 | 98.53 | 100.00 | 0.00 | 1.11 | 71.31 | NaN |
| new_k3_14398 | local | 5399 | NaN | 63.40 | 93.63 | 68.25 | 98.80 | 66.90 | 30.99 | 0.76 | 14.93 | 2.87 |
