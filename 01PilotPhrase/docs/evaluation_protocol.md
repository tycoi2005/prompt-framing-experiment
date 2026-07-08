# Evaluation Protocol (Pilot)

## Objective
Ensure fair comparison across prompt categories and task types while tracking performance and efficiency.

## Unit of Evaluation
One run = one (model, task, prompt variant) triple.

## Primary Metric
- Pass@1 (binary correctness on first response)

## Secondary Metrics
- Prompt tokens
- Completion tokens
- Total tokens
- Latency (seconds)
- Format compliance (yes/no)
- Failure type (logic, syntax/runtime, instruction-following, timeout)

## Experimental Controls
- Fixed model temperature and decoding params per run batch
- Same task set across compared categories
- Prompt length guidance for comparability
- Deterministic test harness and timeout policy

## Pilot Run Design
- Start with 50-100 prompt instances total
- Cover all categories at least once before adding repeats
- Repeat selected anchor categories for variance checks

## Logging Schema
- run_id
- timestamp
- model
- task_id
- category_id
- prompt_variant_id
- correctness
- tokens_prompt
- tokens_completion
- tokens_total
- latency_s
- format_ok
- failure_type
- notes

## Analysis Outputs
- Category-level pass rate table
- Model-by-category interaction table
- Cost/latency vs accuracy plots
- Error-type distribution by category

## Stop/Adjust Rules
- If a category shows near-identical behavior to baseline across tasks, mark for pruning.
- If prompt variants in a category are inconsistent in intent, rewrite before scale-up.
- If >20% runs fail due to formatting or parser issues, fix harness before continuing.
