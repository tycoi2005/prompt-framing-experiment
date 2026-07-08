# Local Model Results Analysis

Analyzed `10800` attempts from `/Users/macos/LearningSpace/ue-courses/Thesis/02ScalingPhrase/localmodel/results`.
Coverage: `6` models, `100` base task ids, `5400` code attempts, `5400` math attempts.

## Overall By Task Type

| kind | n | passed | pass_rate | mean_score | median_duration_seconds | mean_prompt_tokens | mean_completion_tokens | error_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | 5400 | 492 | 9.1% | 0.14 | 9.56 | 291.01 | 564.76 | 62.0% |
| math | 5400 | 1679 | 31.1% | 0.31 | 1.83 | 163.68 | 156.59 | 68.9% |

## Overall By Model

| model_slug | n | passed | pass_rate | mean_score | median_duration_seconds | mean_prompt_tokens | mean_completion_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nemotron-3-nano-4b_1_50 | 1800 | 1026 | 57.0% | 0.61 | 10.58 | 227.70 | 967.37 |
| llama3.1-8b_1_50 | 1800 | 441 | 24.5% | 0.27 | 8.88 | 213.08 | 333.75 |
| qwen2.5-7b_1_50 | 1800 | 331 | 18.4% | 0.20 | 3.48 | 220.42 | 160.78 |
| gemma2-9b_1_50 | 1800 | 239 | 13.3% | 0.17 | 1.78 | 224.60 | 90.66 |
| mistral-7b-instruct_1_50 | 1800 | 73 | 4.1% | 0.05 | 5.34 | 234.65 | 222.44 |
| deepseek-coder-6.7b-instruct_1_50 | 1800 | 61 | 3.4% | 0.04 | 7.18 | 243.61 | 389.07 |

## Model Ranking Within Each Task Type

| kind | model_slug | n | passed | pass_rate | mean_score | pass_rate_ci95_low | pass_rate_ci95_high | median_duration_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | nemotron-3-nano-4b_1_50 | 900 | 205 | 22.8% | 0.30 | 20.2% | 25.6% | 17.78 |
| code | qwen2.5-7b_1_50 | 900 | 119 | 13.2% | 0.17 | 11.2% | 15.6% | 8.75 |
| code | gemma2-9b_1_50 | 900 | 102 | 11.3% | 0.19 | 9.4% | 13.6% | 5.52 |
| code | llama3.1-8b_1_50 | 900 | 52 | 5.8% | 0.11 | 4.4% | 7.5% | 11.16 |
| code | deepseek-coder-6.7b-instruct_1_50 | 900 | 10 | 1.1% | 0.02 | 0.6% | 2.0% | 9.04 |
| code | mistral-7b-instruct_1_50 | 900 | 4 | 0.4% | 0.02 | 0.2% | 1.1% | 9.12 |
| math | nemotron-3-nano-4b_1_50 | 900 | 821 | 91.2% | 0.91 | 89.2% | 92.9% | 3.15 |
| math | llama3.1-8b_1_50 | 900 | 389 | 43.2% | 0.43 | 40.0% | 46.5% | 5.09 |
| math | qwen2.5-7b_1_50 | 900 | 212 | 23.6% | 0.24 | 20.9% | 26.4% | 0.68 |
| math | gemma2-9b_1_50 | 900 | 137 | 15.2% | 0.15 | 13.0% | 17.7% | 0.80 |
| math | mistral-7b-instruct_1_50 | 900 | 69 | 7.7% | 0.08 | 6.1% | 9.6% | 0.89 |
| math | deepseek-coder-6.7b-instruct_1_50 | 900 | 51 | 5.7% | 0.06 | 4.3% | 7.4% | 5.35 |

## Base Tasks Solved By At Least One Prompt Variant

| kind | model_slug | n | passed | pass_rate | mean_score |
| --- | --- | --- | --- | --- | --- |
| code | nemotron-3-nano-4b_1_50 | 50 | 21 | 42.0% | 0.55 |
| code | qwen2.5-7b_1_50 | 50 | 21 | 42.0% | 0.48 |
| code | llama3.1-8b_1_50 | 50 | 15 | 30.0% | 0.41 |
| code | gemma2-9b_1_50 | 50 | 14 | 28.0% | 0.41 |
| code | mistral-7b-instruct_1_50 | 50 | 4 | 8.0% | 0.20 |
| code | deepseek-coder-6.7b-instruct_1_50 | 50 | 3 | 6.0% | 0.15 |
| math | nemotron-3-nano-4b_1_50 | 50 | 48 | 96.0% | 0.96 |
| math | llama3.1-8b_1_50 | 50 | 44 | 88.0% | 0.88 |
| math | deepseek-coder-6.7b-instruct_1_50 | 50 | 21 | 42.0% | 0.42 |
| math | qwen2.5-7b_1_50 | 50 | 21 | 42.0% | 0.42 |
| math | gemma2-9b_1_50 | 50 | 15 | 30.0% | 0.30 |
| math | mistral-7b-instruct_1_50 | 50 | 13 | 26.0% | 0.26 |

## Prompt Factor Main Effects

Variant metadata comes from the prompt matrix: tone is `neutral`, `polite`, or `aggressive`; role is collapsed to `role` versus `no role`; format is `plaintext`, `json`, or `xml`.


| kind | factor | level | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | tone | aggressive | 1800 | 167 | 9.3% | 0.14 | 324.13 |
| code | tone | neutral | 1800 | 167 | 9.3% | 0.14 | 259.63 |
| code | tone | polite | 1800 | 158 | 8.8% | 0.13 | 289.28 |
| math | tone | aggressive | 1800 | 561 | 31.2% | 0.31 | 195.69 |
| math | tone | neutral | 1800 | 544 | 30.2% | 0.30 | 131.86 |
| math | tone | polite | 1800 | 574 | 31.9% | 0.32 | 163.47 |

| kind | factor | level | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | role | no role | 2700 | 260 | 9.6% | 0.14 | 289.22 |
| code | role | role | 2700 | 232 | 8.6% | 0.13 | 292.80 |
| math | role | no role | 2700 | 810 | 30.0% | 0.30 | 161.93 |
| math | role | role | 2700 | 869 | 32.2% | 0.32 | 165.43 |

| kind | factor | level | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | format | json | 1800 | 161 | 8.9% | 0.14 | 293.61 |
| code | format | plaintext | 1800 | 158 | 8.8% | 0.13 | 276.42 |
| code | format | xml | 1800 | 173 | 9.6% | 0.14 | 303.01 |
| math | format | json | 1800 | 523 | 29.1% | 0.29 | 165.91 |
| math | format | plaintext | 1800 | 598 | 33.2% | 0.33 | 151.91 |
| math | format | xml | 1800 | 558 | 31.0% | 0.31 | 173.20 |

## Prompt Factor Contrasts

Deltas compare each level against the natural baseline within the same task type: neutral tone, no role, and plaintext format. P-values use a simple two-proportion z-test.

| kind | factor | baseline | level | baseline_pass_rate | level_pass_rate | delta_pass_rate_pp | z_test_p_value | baseline_mean_score | level_mean_score | delta_mean_score | delta_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | tone | neutral | aggressive | 9.3% | 9.3% | +0.0 pp | 1.0000 | 0.14 | 0.14 | -0.00 | +64.50 |
| code | tone | neutral | polite | 9.3% | 8.8% | -0.5 pp | 0.6007 | 0.14 | 0.13 | -0.01 | +29.66 |
| math | tone | neutral | aggressive | 30.2% | 31.2% | +0.9 pp | 0.5390 | 0.30 | 0.31 | +0.01 | +63.83 |
| math | tone | neutral | polite | 30.2% | 31.9% | +1.7 pp | 0.2799 | 0.30 | 0.32 | +0.02 | +31.61 |
| code | role_binary | no role | role | 9.6% | 8.6% | -1.0 pp | 0.1855 | 0.14 | 0.13 | -0.01 | +3.58 |
| math | role_binary | no role | role | 30.0% | 32.2% | +2.2 pp | 0.0828 | 0.30 | 0.32 | +0.02 | +3.50 |
| code | format | plaintext | json | 8.8% | 8.9% | +0.2 pp | 0.8603 | 0.13 | 0.14 | +0.00 | +17.19 |
| code | format | plaintext | xml | 8.8% | 9.6% | +0.8 pp | 0.3869 | 0.13 | 0.14 | +0.01 | +26.59 |
| math | format | plaintext | json | 33.2% | 29.1% | -4.2 pp | 0.0069 | 0.33 | 0.29 | -0.04 | +14.00 |
| math | format | plaintext | xml | 33.2% | 31.0% | -2.2 pp | 0.1533 | 0.33 | 0.31 | -0.02 | +21.29 |

## Paired Fixed-Effect-Style Contrasts

These contrasts compare each factor level against its baseline within the same model, task kind, and base task. This is a dependency-free approximation of fixed effects for model and task difficulty.

| kind | model_slug | factor | baseline | level | paired_units | mean_score_delta | mean_pass_delta_pp | positive_score_units | negative_score_units | zero_score_units |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | ALL_MODELS_FIXED_BY_TASK | format | plaintext | json | 1800 | 0.01 | +0.0 pp | 174 | 108 | 1518 |
| code | ALL_MODELS_FIXED_BY_TASK | format | plaintext | xml | 1800 | 0.00 | +0.3 pp | 144 | 132 | 1524 |
| code | ALL_MODELS_FIXED_BY_TASK | role_binary | no role | role | 2700 | -0.04 | -3.0 pp | 216 | 288 | 2196 |
| code | ALL_MODELS_FIXED_BY_TASK | tone | neutral | aggressive | 1800 | 0.00 | +1.0 pp | 150 | 138 | 1512 |
| code | ALL_MODELS_FIXED_BY_TASK | tone | neutral | polite | 1800 | 0.04 | +3.7 pp | 204 | 138 | 1458 |
| math | ALL_MODELS_FIXED_BY_TASK | format | plaintext | json | 1800 | -0.02 | -1.7 pp | 78 | 108 | 1614 |
| math | ALL_MODELS_FIXED_BY_TASK | format | plaintext | xml | 1800 | 0.00 | +0.3 pp | 96 | 90 | 1614 |
| math | ALL_MODELS_FIXED_BY_TASK | role_binary | no role | role | 2700 | 0.04 | +3.7 pp | 234 | 135 | 2331 |
| math | ALL_MODELS_FIXED_BY_TASK | tone | neutral | aggressive | 1800 | 0.01 | +0.7 pp | 102 | 90 | 1608 |
| math | ALL_MODELS_FIXED_BY_TASK | tone | neutral | polite | 1800 | -0.02 | -1.7 pp | 42 | 72 | 1686 |

## Prompt Factor Interactions

| kind | factor_a | level_a | factor_b | level_b | n | passed | pass_rate | mean_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | role_binary | no role | format | xml | 900 | 90 | 10.0% | 0.15 |
| code | role_binary | no role | format | json | 900 | 87 | 9.7% | 0.14 |
| code | role_binary | no role | format | plaintext | 900 | 83 | 9.2% | 0.14 |
| code | role_binary | role | format | xml | 900 | 83 | 9.2% | 0.14 |
| code | role_binary | role | format | plaintext | 900 | 75 | 8.3% | 0.12 |
| code | role_binary | role | format | json | 900 | 74 | 8.2% | 0.13 |
| code | tone | aggressive | format | xml | 600 | 61 | 10.2% | 0.15 |
| code | tone | neutral | format | plaintext | 600 | 60 | 10.0% | 0.15 |
| code | tone | polite | format | json | 600 | 59 | 9.8% | 0.14 |
| code | tone | polite | format | xml | 600 | 57 | 9.5% | 0.14 |
| code | tone | aggressive | format | plaintext | 600 | 56 | 9.3% | 0.14 |
| code | tone | neutral | format | xml | 600 | 55 | 9.2% | 0.14 |
| code | tone | neutral | format | json | 600 | 52 | 8.7% | 0.14 |
| code | tone | aggressive | format | json | 600 | 50 | 8.3% | 0.13 |
| code | tone | polite | format | plaintext | 600 | 42 | 7.0% | 0.11 |
| code | tone | aggressive | role_binary | no role | 900 | 91 | 10.1% | 0.15 |
| code | tone | neutral | role_binary | no role | 900 | 89 | 9.9% | 0.15 |
| code | tone | polite | role_binary | no role | 900 | 80 | 8.9% | 0.13 |
| code | tone | neutral | role_binary | role | 900 | 78 | 8.7% | 0.13 |
| code | tone | polite | role_binary | role | 900 | 78 | 8.7% | 0.13 |
| code | tone | aggressive | role_binary | role | 900 | 76 | 8.4% | 0.13 |
| math | role_binary | role | format | plaintext | 900 | 304 | 33.8% | 0.34 |
| math | role_binary | no role | format | plaintext | 900 | 294 | 32.7% | 0.33 |
| math | role_binary | role | format | xml | 900 | 291 | 32.3% | 0.32 |
| math | role_binary | role | format | json | 900 | 274 | 30.4% | 0.30 |
| math | role_binary | no role | format | xml | 900 | 267 | 29.7% | 0.30 |
| math | role_binary | no role | format | json | 900 | 249 | 27.7% | 0.28 |
| math | tone | polite | format | plaintext | 600 | 212 | 35.3% | 0.35 |
| math | tone | aggressive | format | plaintext | 600 | 193 | 32.2% | 0.32 |
| math | tone | neutral | format | plaintext | 600 | 193 | 32.2% | 0.32 |
| math | tone | aggressive | format | xml | 600 | 189 | 31.5% | 0.32 |
| math | tone | polite | format | xml | 600 | 186 | 31.0% | 0.31 |
| math | tone | neutral | format | xml | 600 | 183 | 30.5% | 0.30 |
| math | tone | aggressive | format | json | 600 | 179 | 29.8% | 0.30 |
| math | tone | polite | format | json | 600 | 176 | 29.3% | 0.29 |
| math | tone | neutral | format | json | 600 | 168 | 28.0% | 0.28 |

## Model-Specific Factor Behavior

These rows show where the same prompt factor behaves differently depending on model. `range_delta_pp` is the gap between the most-helped and most-hurt model for that factor level.

| kind | factor | level | models | mean_delta_pp | min_delta_pp | min_model | max_delta_pp | max_model | range_delta_pp | positive_models | negative_models | p_lt_0_05_models |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | tone | aggressive | 6 | +0.0 pp | -2.0 pp | llama3.1-8b_1_50 | +2.0 pp | deepseek-coder-6.7b-instruct_1_50 | +4.0 pp | 4 | 2 | 1 |
| code | format | xml | 6 | +0.8 pp | +0.0 pp | gemma2-9b_1_50 | +3.7 pp | nemotron-3-nano-4b_1_50 | +3.7 pp | 4 | 0 | 0 |
| code | tone | polite | 6 | -0.5 pp | -2.7 pp | llama3.1-8b_1_50 | +0.3 pp | deepseek-coder-6.7b-instruct_1_50 | +3.0 pp | 2 | 2 | 0 |
| code | role_binary | role | 6 | -1.0 pp | -2.2 pp | gemma2-9b_1_50 | +0.4 pp | llama3.1-8b_1_50 | +2.7 pp | 1 | 5 | 0 |
| code | format | json | 6 | +0.2 pp | -1.0 pp | gemma2-9b_1_50 | +1.0 pp | deepseek-coder-6.7b-instruct_1_50 | +2.0 pp | 3 | 2 | 0 |
| math | format | json | 6 | -4.2 pp | -15.7 pp | llama3.1-8b_1_50 | +1.3 pp | nemotron-3-nano-4b_1_50 | +17.0 pp | 1 | 4 | 2 |
| math | format | xml | 6 | -2.2 pp | -9.7 pp | llama3.1-8b_1_50 | +5.7 pp | qwen2.5-7b_1_50 | +15.3 pp | 2 | 4 | 2 |
| math | role_binary | role | 6 | +2.2 pp | -0.7 pp | deepseek-coder-6.7b-instruct_1_50 | +10.2 pp | qwen2.5-7b_1_50 | +10.9 pp | 5 | 1 | 1 |
| math | tone | polite | 6 | +1.7 pp | -1.7 pp | nemotron-3-nano-4b_1_50 | +5.3 pp | llama3.1-8b_1_50 | +7.0 pp | 4 | 2 | 1 |
| math | tone | aggressive | 6 | +0.9 pp | -0.7 pp | nemotron-3-nano-4b_1_50 | +2.3 pp | deepseek-coder-6.7b-instruct_1_50 | +3.0 pp | 4 | 2 | 0 |

## Best Factor Level By Model

| kind | model_slug | factor | best_level | best_pass_rate | worst_level | worst_pass_rate | spread_pp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | nemotron-3-nano-4b_1_50 | format | xml | 25.0% | plaintext | 21.3% | +3.7 pp |
| code | llama3.1-8b_1_50 | format | xml | 6.3% | json | 5.3% | +1.0 pp |
| code | deepseek-coder-6.7b-instruct_1_50 | format | json | 1.7% | plaintext | 0.7% | +1.0 pp |
| code | gemma2-9b_1_50 | format | plaintext | 11.7% | json | 10.7% | +1.0 pp |
| code | qwen2.5-7b_1_50 | format | json | 13.7% | plaintext | 13.0% | +0.7 pp |
| code | mistral-7b-instruct_1_50 | format | xml | 0.7% | json | 0.3% | +0.3 pp |
| code | gemma2-9b_1_50 | role_binary | no role | 12.4% | role | 10.2% | +2.2 pp |
| code | nemotron-3-nano-4b_1_50 | role_binary | no role | 23.6% | role | 22.0% | +1.6 pp |
| code | deepseek-coder-6.7b-instruct_1_50 | role_binary | no role | 1.8% | role | 0.4% | +1.3 pp |
| code | qwen2.5-7b_1_50 | role_binary | no role | 13.8% | role | 12.7% | +1.1 pp |
| code | llama3.1-8b_1_50 | role_binary | role | 6.0% | no role | 5.6% | +0.4 pp |
| code | mistral-7b-instruct_1_50 | role_binary | no role | 0.7% | role | 0.2% | +0.4 pp |
| code | llama3.1-8b_1_50 | tone | neutral | 7.3% | polite | 4.7% | +2.7 pp |
| code | deepseek-coder-6.7b-instruct_1_50 | tone | aggressive | 2.3% | neutral | 0.3% | +2.0 pp |
| code | gemma2-9b_1_50 | tone | neutral | 12.0% | aggressive | 10.0% | +2.0 pp |
| code | qwen2.5-7b_1_50 | tone | aggressive | 14.0% | polite | 12.3% | +1.7 pp |
| code | mistral-7b-instruct_1_50 | tone | aggressive | 1.0% | neutral | 0.0% | +1.0 pp |
| code | nemotron-3-nano-4b_1_50 | tone | aggressive | 23.0% | neutral | 22.7% | +0.3 pp |
| math | llama3.1-8b_1_50 | format | plaintext | 51.7% | json | 36.0% | +15.7 pp |
| math | qwen2.5-7b_1_50 | format | xml | 27.7% | json | 21.0% | +6.7 pp |
| math | deepseek-coder-6.7b-instruct_1_50 | format | plaintext | 9.0% | xml | 3.3% | +5.7 pp |
| math | gemma2-9b_1_50 | format | plaintext | 18.3% | json | 13.0% | +5.3 pp |
| math | nemotron-3-nano-4b_1_50 | format | json | 92.3% | xml | 90.3% | +2.0 pp |
| math | mistral-7b-instruct_1_50 | format | xml | 8.3% | json | 7.3% | +1.0 pp |
| math | qwen2.5-7b_1_50 | role_binary | role | 28.7% | no role | 18.4% | +10.2 pp |
| math | nemotron-3-nano-4b_1_50 | role_binary | role | 91.8% | no role | 90.7% | +1.1 pp |
| math | mistral-7b-instruct_1_50 | role_binary | role | 8.2% | no role | 7.1% | +1.1 pp |
| math | llama3.1-8b_1_50 | role_binary | role | 43.8% | no role | 42.7% | +1.1 pp |
| math | deepseek-coder-6.7b-instruct_1_50 | role_binary | no role | 6.0% | role | 5.3% | +0.7 pp |
| math | gemma2-9b_1_50 | role_binary | role | 15.3% | no role | 15.1% | +0.2 pp |
| math | llama3.1-8b_1_50 | tone | polite | 46.3% | neutral | 41.0% | +5.3 pp |
| math | deepseek-coder-6.7b-instruct_1_50 | tone | polite | 8.0% | neutral | 3.3% | +4.7 pp |
| math | gemma2-9b_1_50 | tone | aggressive | 16.3% | neutral | 14.0% | +2.3 pp |
| math | nemotron-3-nano-4b_1_50 | tone | neutral | 92.0% | polite | 90.3% | +1.7 pp |
| math | qwen2.5-7b_1_50 | tone | aggressive | 24.3% | polite | 23.0% | +1.3 pp |
| math | mistral-7b-instruct_1_50 | tone | polite | 8.3% | aggressive | 7.0% | +1.3 pp |

## Math Versus Code Factor Differences

This compares the same factor level within the same model across task kind. Positive `math_minus_code_delta_pp` means the factor helped math more, or hurt math less, than it helped code. The table also compares prompt-token, completion-token, and duration deltas.

| model_slug | factor | level | code_delta_pp | math_delta_pp | math_minus_code_delta_pp | math_minus_code_prompt_tokens | math_minus_code_completion_tokens | math_minus_code_duration_seconds | code_p_value | math_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| llama3.1-8b_1_50 | format | json | -0.3 pp | -15.7 pp | -15.3 pp | -3.38 | -110.46 | -3.19 | 0.8579 | 0.0001 |
| qwen2.5-7b_1_50 | role_binary | role | -1.1 pp | +10.2 pp | +11.3 pp | -1.00 | -21.26 | -0.58 | 0.6227 | 0.0003 |
| llama3.1-8b_1_50 | format | xml | +0.7 pp | -9.7 pp | -10.3 pp | -5.04 | 28.72 | 0.82 | 0.7310 | 0.0177 |
| llama3.1-8b_1_50 | tone | polite | -2.7 pp | +5.3 pp | +8.0 pp | 3.00 | -14.93 | -0.39 | 0.1691 | 0.1878 |
| deepseek-coder-6.7b-instruct_1_50 | format | xml | +0.3 pp | -5.7 pp | -6.0 pp | -5.14 | 4.12 | -0.52 | 0.6534 | 0.0039 |
| qwen2.5-7b_1_50 | format | xml | +0.0 pp | +5.7 pp | +5.7 pp | -5.04 | -13.30 | -0.35 | 1.0000 | 0.1082 |
| deepseek-coder-6.7b-instruct_1_50 | format | json | +1.0 pp | -4.3 pp | -5.3 pp | -2.64 | 1.11 | -0.55 | 0.2541 | 0.0354 |
| nemotron-3-nano-4b_1_50 | format | xml | +3.7 pp | -0.7 pp | -4.3 pp | -6.33 | 62.64 | 1.35 | 0.2871 | 0.7790 |
| deepseek-coder-6.7b-instruct_1_50 | tone | polite | +0.3 pp | +4.7 pp | +4.3 pp | 1.00 | 11.89 | 0.78 | 0.5627 | 0.0134 |
| gemma2-9b_1_50 | format | json | -1.0 pp | -5.3 pp | -4.3 pp | -3.44 | 3.75 | 0.15 | 0.6974 | 0.0723 |
| gemma2-9b_1_50 | tone | aggressive | -2.0 pp | +2.3 pp | +4.3 pp | -1.00 | -7.43 | -0.14 | 0.4337 | 0.4256 |
| gemma2-9b_1_50 | format | xml | +0.0 pp | -4.0 pp | -4.0 pp | -5.08 | 6.93 | 0.20 | 1.0000 | 0.1851 |
| llama3.1-8b_1_50 | tone | aggressive | -2.0 pp | +1.3 pp | +3.3 pp | -0.00 | 43.44 | 1.35 | 0.3146 | 0.7405 |
| nemotron-3-nano-4b_1_50 | role_binary | role | -1.6 pp | +1.1 pp | +2.7 pp | -1.49 | -44.45 | -0.48 | 0.5780 | 0.5559 |
| gemma2-9b_1_50 | role_binary | role | -2.2 pp | +0.2 pp | +2.4 pp | -1.00 | 2.41 | 0.07 | 0.2930 | 0.9261 |
| nemotron-3-nano-4b_1_50 | tone | polite | +0.0 pp | -1.7 pp | -1.7 pp | 2.73 | 67.74 | 0.81 | 1.0000 | 0.4720 |
| qwen2.5-7b_1_50 | format | json | +0.7 pp | -1.0 pp | -1.7 pp | -3.38 | -12.36 | -0.34 | 0.8102 | 0.7656 |
| mistral-7b-instruct_1_50 | tone | aggressive | +1.0 pp | -0.7 pp | -1.7 pp | -1.00 | -16.43 | -0.35 | 0.0825 | 0.7541 |
| mistral-7b-instruct_1_50 | role_binary | role | -0.4 pp | +1.1 pp | +1.6 pp | 3.00 | 33.03 | 0.82 | 0.3162 | 0.5310 |
| gemma2-9b_1_50 | tone | polite | +0.0 pp | +1.3 pp | +1.3 pp | 2.00 | -12.73 | -0.37 | 1.0000 | 0.6444 |
| nemotron-3-nano-4b_1_50 | tone | aggressive | +0.3 pp | -0.7 pp | -1.0 pp | 0.00 | -35.35 | -0.53 | 0.9225 | 0.7677 |
| deepseek-coder-6.7b-instruct_1_50 | role_binary | role | -1.3 pp | -0.7 pp | +0.7 pp | 1.00 | 17.54 | 0.71 | 0.0564 | 0.6654 |
| qwen2.5-7b_1_50 | tone | polite | -1.0 pp | -0.3 pp | +0.7 pp | 3.00 | -37.26 | -1.00 | 0.7142 | 0.9229 |
| mistral-7b-instruct_1_50 | format | xml | +0.3 pp | +1.0 pp | +0.7 pp | -5.14 | 45.10 | 1.12 | 0.5627 | 0.6485 |
| nemotron-3-nano-4b_1_50 | format | json | +0.7 pp | +1.3 pp | +0.7 pp | -3.79 | 14.10 | 0.55 | 0.8429 | 0.5546 |
| llama3.1-8b_1_50 | role_binary | role | +0.4 pp | +1.1 pp | +0.7 pp | -1.00 | -15.39 | -0.44 | 0.7751 | 0.7365 |
| mistral-7b-instruct_1_50 | tone | polite | +0.3 pp | +0.7 pp | +0.3 pp | 0.00 | -92.77 | -2.28 | 0.3169 | 0.7634 |
| deepseek-coder-6.7b-instruct_1_50 | tone | aggressive | +2.0 pp | +2.3 pp | +0.3 pp | -2.00 | 24.10 | 0.43 | 0.0327 | 0.1680 |
| qwen2.5-7b_1_50 | tone | aggressive | +0.7 pp | +1.0 pp | +0.3 pp | -0.00 | 9.71 | 0.39 | 0.8121 | 0.7738 |
| mistral-7b-instruct_1_50 | format | json | +0.0 pp | +0.0 pp | +0.0 pp | -2.48 | 6.41 | 0.17 | 1.0000 | 1.0000 |

## Behavior And Error Analysis

This checks whether prompt factors change output behavior, not only correctness.

| grouping | kind | tone | format | role_binary | n | pass_rate | mean_score | mean_completion_tokens | mean_duration_seconds | code_only_rate | extraction_failure_rate | runtime_failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kind | code |  |  |  | 5400 | 9.1% | 0.14 | 564.76 | 12.24 | 72.9% | 0.3% | 54.7% |
| kind | math |  |  |  | 5400 | 31.1% | 0.31 | 156.59 | 3.89 | 0.0% | 0.0% | 0.0% |
| kind+tone | code | aggressive |  |  | 1800 | 9.3% | 0.14 | 557.50 | 11.99 | 74.3% | 0.3% | 53.4% |
| kind+tone | code | neutral |  |  | 1800 | 9.3% | 0.14 | 553.57 | 11.89 | 75.7% | 0.4% | 53.0% |
| kind+tone | code | polite |  |  | 1800 | 8.8% | 0.13 | 583.21 | 12.85 | 68.7% | 0.1% | 57.8% |
| kind+tone | math | aggressive |  |  | 1800 | 31.2% | 0.31 | 155.68 | 3.90 | 0.0% | 0.0% | 0.0% |
| kind+tone | math | neutral |  |  | 1800 | 30.2% | 0.30 | 148.74 | 3.61 | 0.0% | 0.0% | 0.0% |
| kind+tone | math | polite |  |  | 1800 | 31.9% | 0.32 | 165.37 | 4.16 | 0.0% | 0.0% | 0.0% |
| kind+role_binary | code |  |  | no role | 2700 | 9.6% | 0.14 | 557.03 | 12.11 | 73.4% | 0.2% | 53.6% |
| kind+role_binary | code |  |  | role | 2700 | 8.6% | 0.13 | 572.49 | 12.38 | 72.3% | 0.3% | 55.9% |
| kind+role_binary | math |  |  | no role | 2700 | 30.0% | 0.30 | 151.21 | 3.74 | 0.0% | 0.0% | 0.0% |
| kind+role_binary | math |  |  | role | 2700 | 32.2% | 0.32 | 161.98 | 4.03 | 0.0% | 0.0% | 0.0% |
| kind+format | code |  | json |  | 1800 | 8.9% | 0.14 | 561.45 | 12.14 | 73.5% | 0.2% | 52.9% |
| kind+format | code |  | plaintext |  | 1800 | 8.8% | 0.13 | 576.96 | 12.53 | 68.9% | 0.3% | 56.9% |
| kind+format | code |  | xml |  | 1800 | 9.6% | 0.14 | 555.87 | 12.06 | 76.2% | 0.3% | 54.4% |
| kind+format | math |  | json |  | 1800 | 29.1% | 0.29 | 135.00 | 3.28 | 0.0% | 0.0% | 0.0% |
| kind+format | math |  | plaintext |  | 1800 | 33.2% | 0.33 | 166.75 | 4.20 | 0.0% | 0.0% | 0.0% |
| kind+format | math |  | xml |  | 1800 | 31.0% | 0.31 | 168.03 | 4.18 | 0.0% | 0.0% | 0.0% |

Frequent non-success error categories:

| grouping | kind | tone | error_category | n | rate_within_group |
| --- | --- | --- | --- | --- | --- |
| kind+error_category | code |  | invalid_python | 207 | 3.8% |
| kind+error_category | code |  | missing_or_empty_code | 14 | 0.3% |
| kind+error_category | code |  | name_not_defined | 2674 | 49.5% |
| kind+error_category | code |  | timeout | 61 | 1.1% |
| kind+error_category | code |  | wrong_answer | 390 | 7.2% |
| kind+error_category | math |  | wrong_answer | 3721 | 68.9% |
| kind+tone+error_category | code | aggressive | invalid_python | 74 | 4.1% |
| kind+tone+error_category | code | aggressive | missing_or_empty_code | 5 | 0.3% |
| kind+tone+error_category | code | aggressive | name_not_defined | 861 | 47.8% |
| kind+tone+error_category | code | aggressive | timeout | 22 | 1.2% |
| kind+tone+error_category | code | aggressive | wrong_answer | 132 | 7.3% |
| kind+tone+error_category | code | neutral | invalid_python | 55 | 3.1% |
| kind+tone+error_category | code | neutral | missing_or_empty_code | 8 | 0.4% |
| kind+tone+error_category | code | neutral | name_not_defined | 871 | 48.4% |
| kind+tone+error_category | code | neutral | timeout | 20 | 1.1% |
| kind+tone+error_category | code | neutral | wrong_answer | 136 | 7.6% |
| kind+tone+error_category | code | polite | invalid_python | 78 | 4.3% |
| kind+tone+error_category | code | polite | missing_or_empty_code | 1 | 0.1% |
| kind+tone+error_category | code | polite | name_not_defined | 942 | 52.3% |
| kind+tone+error_category | code | polite | timeout | 19 | 1.1% |
| kind+tone+error_category | code | polite | wrong_answer | 122 | 6.8% |
| kind+tone+error_category | math | aggressive | wrong_answer | 1239 | 68.8% |
| kind+tone+error_category | math | neutral | wrong_answer | 1256 | 69.8% |
| kind+tone+error_category | math | polite | wrong_answer | 1226 | 68.1% |

## Dataset Shift: Pilot Versus Scaled Study

This compares the old 3-model code-only pilot against the scaled study. `scaled_common3_code` keeps only Gemma, Llama, and Qwen code rows to make the closest comparison.

| grouping | dataset | kind | tone | format | n | models | base_tasks | pass_rate | mean_score | mean_completion_tokens | mean_duration_seconds | code_only_rate | runtime_failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dataset | pilot_codeonly |  |  |  | 2700 | 3 | 50 | 10.3% | 0.16 | 289.57 | 9.00 | 99.5% | 39.9% |
| dataset | scaled_all |  |  |  | 10800 | 6 | 100 | 20.1% | 0.22 | 360.68 | 8.07 | 36.4% | 27.4% |
| dataset | scaled_common3_code |  |  |  | 2700 | 3 | 50 | 10.1% | 0.16 | 295.05 | 9.02 | 99.6% | 40.4% |
| dataset+kind | pilot_codeonly | code |  |  | 2700 | 3 | 50 | 10.3% | 0.16 | 289.57 | 9.00 | 99.5% | 39.9% |
| dataset+kind | scaled_all | code |  |  | 5400 | 6 | 50 | 9.1% | 0.14 | 564.76 | 12.24 | 72.9% | 54.7% |
| dataset+kind | scaled_all | math |  |  | 5400 | 6 | 50 | 31.1% | 0.31 | 156.59 | 3.89 | 0.0% | 0.0% |
| dataset+kind | scaled_common3_code | code |  |  | 2700 | 3 | 50 | 10.1% | 0.16 | 295.05 | 9.02 | 99.6% | 40.4% |
| dataset+kind+tone | pilot_codeonly | code | aggressive |  | 900 | 3 | 50 | 9.2% | 0.14 | 280.83 | 8.71 | 99.8% | 39.4% |
| dataset+kind+tone | pilot_codeonly | code | neutral |  | 900 | 3 | 50 | 12.3% | 0.18 | 260.35 | 8.19 | 99.1% | 33.4% |
| dataset+kind+tone | pilot_codeonly | code | polite |  | 900 | 3 | 50 | 9.2% | 0.15 | 327.54 | 10.11 | 99.6% | 46.9% |
| dataset+kind+tone | scaled_all | code | aggressive |  | 1800 | 6 | 50 | 9.3% | 0.14 | 557.50 | 11.99 | 74.3% | 53.4% |
| dataset+kind+tone | scaled_all | code | neutral |  | 1800 | 6 | 50 | 9.3% | 0.14 | 553.57 | 11.89 | 75.7% | 53.0% |
| dataset+kind+tone | scaled_all | code | polite |  | 1800 | 6 | 50 | 8.8% | 0.13 | 583.21 | 12.85 | 68.7% | 57.8% |
| dataset+kind+tone | scaled_all | math | aggressive |  | 1800 | 6 | 50 | 31.2% | 0.31 | 155.68 | 3.90 | 0.0% | 0.0% |
| dataset+kind+tone | scaled_all | math | neutral |  | 1800 | 6 | 50 | 30.2% | 0.30 | 148.74 | 3.61 | 0.0% | 0.0% |
| dataset+kind+tone | scaled_all | math | polite |  | 1800 | 6 | 50 | 31.9% | 0.32 | 165.37 | 4.16 | 0.0% | 0.0% |
| dataset+kind+tone | scaled_common3_code | code | aggressive |  | 900 | 3 | 50 | 9.8% | 0.15 | 285.52 | 8.73 | 99.8% | 40.1% |
| dataset+kind+tone | scaled_common3_code | code | neutral |  | 900 | 3 | 50 | 10.9% | 0.17 | 281.23 | 8.63 | 99.1% | 36.2% |
| dataset+kind+tone | scaled_common3_code | code | polite |  | 900 | 3 | 50 | 9.7% | 0.15 | 318.39 | 9.71 | 99.8% | 44.8% |
| dataset+kind+format | pilot_codeonly | code |  | json | 900 | 3 | 50 | 9.2% | 0.15 | 286.21 | 8.91 | 99.2% | 39.7% |
| dataset+kind+format | pilot_codeonly | code |  | plaintext | 900 | 3 | 50 | 10.3% | 0.15 | 290.02 | 9.01 | 99.8% | 40.6% |
| dataset+kind+format | pilot_codeonly | code |  | xml | 900 | 3 | 50 | 11.2% | 0.17 | 292.50 | 9.10 | 99.4% | 39.6% |
| dataset+kind+format | scaled_all | code |  | json | 1800 | 6 | 50 | 8.9% | 0.14 | 561.45 | 12.14 | 73.5% | 52.9% |
| dataset+kind+format | scaled_all | code |  | plaintext | 1800 | 6 | 50 | 8.8% | 0.13 | 576.96 | 12.53 | 68.9% | 56.9% |
| dataset+kind+format | scaled_all | code |  | xml | 1800 | 6 | 50 | 9.6% | 0.14 | 555.87 | 12.06 | 76.2% | 54.4% |
| dataset+kind+format | scaled_all | math |  | json | 1800 | 6 | 50 | 29.1% | 0.29 | 135.00 | 3.28 | 0.0% | 0.0% |
| dataset+kind+format | scaled_all | math |  | plaintext | 1800 | 6 | 50 | 33.2% | 0.33 | 166.75 | 4.20 | 0.0% | 0.0% |
| dataset+kind+format | scaled_all | math |  | xml | 1800 | 6 | 50 | 31.0% | 0.31 | 168.03 | 4.18 | 0.0% | 0.0% |
| dataset+kind+format | scaled_common3_code | code |  | json | 900 | 3 | 50 | 9.9% | 0.16 | 293.31 | 8.97 | 99.4% | 38.6% |
| dataset+kind+format | scaled_common3_code | code |  | plaintext | 900 | 3 | 50 | 10.1% | 0.16 | 296.72 | 9.07 | 99.7% | 42.8% |
| dataset+kind+format | scaled_common3_code | code |  | xml | 900 | 3 | 50 | 10.3% | 0.16 | 295.11 | 9.03 | 99.6% | 39.8% |

## Model-Specific Factor Contrasts

| kind | model_slug | factor | baseline | level | baseline_pass_rate | level_pass_rate | delta_pass_rate_pp | z_test_p_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| code | deepseek-coder-6.7b-instruct_1_50 | format | plaintext | json | 0.7% | 1.7% | +1.0 pp | 0.2541 |
| code | gemma2-9b_1_50 | format | plaintext | json | 11.7% | 10.7% | -1.0 pp | 0.6974 |
| code | nemotron-3-nano-4b_1_50 | format | plaintext | json | 21.3% | 22.0% | +0.7 pp | 0.8429 |
| code | qwen2.5-7b_1_50 | format | plaintext | json | 13.0% | 13.7% | +0.7 pp | 0.8102 |
| code | llama3.1-8b_1_50 | format | plaintext | json | 5.7% | 5.3% | -0.3 pp | 0.8579 |
| code | mistral-7b-instruct_1_50 | format | plaintext | json | 0.3% | 0.3% | +0.0 pp | 1.0000 |
| code | nemotron-3-nano-4b_1_50 | format | plaintext | xml | 21.3% | 25.0% | +3.7 pp | 0.2871 |
| code | llama3.1-8b_1_50 | format | plaintext | xml | 5.7% | 6.3% | +0.7 pp | 0.7310 |
| code | mistral-7b-instruct_1_50 | format | plaintext | xml | 0.3% | 0.7% | +0.3 pp | 0.5627 |
| code | deepseek-coder-6.7b-instruct_1_50 | format | plaintext | xml | 0.7% | 1.0% | +0.3 pp | 0.6534 |
| code | gemma2-9b_1_50 | format | plaintext | xml | 11.7% | 11.7% | +0.0 pp | 1.0000 |
| code | qwen2.5-7b_1_50 | format | plaintext | xml | 13.0% | 13.0% | +0.0 pp | 1.0000 |
| code | gemma2-9b_1_50 | role_binary | no role | role | 12.4% | 10.2% | -2.2 pp | 0.2930 |
| code | nemotron-3-nano-4b_1_50 | role_binary | no role | role | 23.6% | 22.0% | -1.6 pp | 0.5780 |
| code | deepseek-coder-6.7b-instruct_1_50 | role_binary | no role | role | 1.8% | 0.4% | -1.3 pp | 0.0564 |
| code | qwen2.5-7b_1_50 | role_binary | no role | role | 13.8% | 12.7% | -1.1 pp | 0.6227 |
| code | llama3.1-8b_1_50 | role_binary | no role | role | 5.6% | 6.0% | +0.4 pp | 0.7751 |
| code | mistral-7b-instruct_1_50 | role_binary | no role | role | 0.7% | 0.2% | -0.4 pp | 0.3162 |
| code | deepseek-coder-6.7b-instruct_1_50 | tone | neutral | aggressive | 0.3% | 2.3% | +2.0 pp | 0.0327 |
| code | llama3.1-8b_1_50 | tone | neutral | aggressive | 7.3% | 5.3% | -2.0 pp | 0.3146 |
| code | gemma2-9b_1_50 | tone | neutral | aggressive | 12.0% | 10.0% | -2.0 pp | 0.4337 |
| code | mistral-7b-instruct_1_50 | tone | neutral | aggressive | 0.0% | 1.0% | +1.0 pp | 0.0825 |
| code | qwen2.5-7b_1_50 | tone | neutral | aggressive | 13.3% | 14.0% | +0.7 pp | 0.8121 |
| code | nemotron-3-nano-4b_1_50 | tone | neutral | aggressive | 22.7% | 23.0% | +0.3 pp | 0.9225 |
| code | llama3.1-8b_1_50 | tone | neutral | polite | 7.3% | 4.7% | -2.7 pp | 0.1691 |
| code | qwen2.5-7b_1_50 | tone | neutral | polite | 13.3% | 12.3% | -1.0 pp | 0.7142 |
| code | deepseek-coder-6.7b-instruct_1_50 | tone | neutral | polite | 0.3% | 0.7% | +0.3 pp | 0.5627 |
| code | mistral-7b-instruct_1_50 | tone | neutral | polite | 0.0% | 0.3% | +0.3 pp | 0.3169 |
| code | gemma2-9b_1_50 | tone | neutral | polite | 12.0% | 12.0% | +0.0 pp | 1.0000 |
| code | nemotron-3-nano-4b_1_50 | tone | neutral | polite | 22.7% | 22.7% | +0.0 pp | 1.0000 |
| math | llama3.1-8b_1_50 | format | plaintext | json | 51.7% | 36.0% | -15.7 pp | 0.0001 |
| math | gemma2-9b_1_50 | format | plaintext | json | 18.3% | 13.0% | -5.3 pp | 0.0723 |
| math | deepseek-coder-6.7b-instruct_1_50 | format | plaintext | json | 9.0% | 4.7% | -4.3 pp | 0.0354 |
| math | nemotron-3-nano-4b_1_50 | format | plaintext | json | 91.0% | 92.3% | +1.3 pp | 0.5546 |
| math | qwen2.5-7b_1_50 | format | plaintext | json | 22.0% | 21.0% | -1.0 pp | 0.7656 |
| math | mistral-7b-instruct_1_50 | format | plaintext | json | 7.3% | 7.3% | +0.0 pp | 1.0000 |
| math | llama3.1-8b_1_50 | format | plaintext | xml | 51.7% | 42.0% | -9.7 pp | 0.0177 |
| math | qwen2.5-7b_1_50 | format | plaintext | xml | 22.0% | 27.7% | +5.7 pp | 0.1082 |
| math | deepseek-coder-6.7b-instruct_1_50 | format | plaintext | xml | 9.0% | 3.3% | -5.7 pp | 0.0039 |
| math | gemma2-9b_1_50 | format | plaintext | xml | 18.3% | 14.3% | -4.0 pp | 0.1851 |
| math | mistral-7b-instruct_1_50 | format | plaintext | xml | 7.3% | 8.3% | +1.0 pp | 0.6485 |
| math | nemotron-3-nano-4b_1_50 | format | plaintext | xml | 91.0% | 90.3% | -0.7 pp | 0.7790 |
| math | qwen2.5-7b_1_50 | role_binary | no role | role | 18.4% | 28.7% | +10.2 pp | 0.0003 |
| math | nemotron-3-nano-4b_1_50 | role_binary | no role | role | 90.7% | 91.8% | +1.1 pp | 0.5559 |
| math | mistral-7b-instruct_1_50 | role_binary | no role | role | 7.1% | 8.2% | +1.1 pp | 0.5310 |
| math | llama3.1-8b_1_50 | role_binary | no role | role | 42.7% | 43.8% | +1.1 pp | 0.7365 |
| math | deepseek-coder-6.7b-instruct_1_50 | role_binary | no role | role | 6.0% | 5.3% | -0.7 pp | 0.6654 |
| math | gemma2-9b_1_50 | role_binary | no role | role | 15.1% | 15.3% | +0.2 pp | 0.9261 |
| math | deepseek-coder-6.7b-instruct_1_50 | tone | neutral | aggressive | 3.3% | 5.7% | +2.3 pp | 0.1680 |
| math | gemma2-9b_1_50 | tone | neutral | aggressive | 14.0% | 16.3% | +2.3 pp | 0.4256 |
| math | llama3.1-8b_1_50 | tone | neutral | aggressive | 41.0% | 42.3% | +1.3 pp | 0.7405 |
| math | qwen2.5-7b_1_50 | tone | neutral | aggressive | 23.3% | 24.3% | +1.0 pp | 0.7738 |
| math | nemotron-3-nano-4b_1_50 | tone | neutral | aggressive | 92.0% | 91.3% | -0.7 pp | 0.7677 |
| math | mistral-7b-instruct_1_50 | tone | neutral | aggressive | 7.7% | 7.0% | -0.7 pp | 0.7541 |
| math | llama3.1-8b_1_50 | tone | neutral | polite | 41.0% | 46.3% | +5.3 pp | 0.1878 |
| math | deepseek-coder-6.7b-instruct_1_50 | tone | neutral | polite | 3.3% | 8.0% | +4.7 pp | 0.0134 |
| math | nemotron-3-nano-4b_1_50 | tone | neutral | polite | 92.0% | 90.3% | -1.7 pp | 0.4720 |
| math | gemma2-9b_1_50 | tone | neutral | polite | 14.0% | 15.3% | +1.3 pp | 0.6444 |
| math | mistral-7b-instruct_1_50 | tone | neutral | polite | 7.7% | 8.3% | +0.7 pp | 0.7634 |
| math | qwen2.5-7b_1_50 | tone | neutral | polite | 23.3% | 23.0% | -0.3 pp | 0.9229 |

## Factor Takeaways

- code: largest gain was format=xml (+0.8 pp); largest drop was role_binary=role (-1.0 pp).
- math: largest gain was role_binary=role (+2.2 pp); largest drop was format=json (-4.2 pp).

## Strongest Prompt Variants

Code:

| kind | variant_id | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- |
| code | 15 | 300 | 35 | 11.7% | 0.16 | 334.37 |
| code | 8 | 300 | 34 | 11.3% | 0.15 | 290.36 |
| code | 12 | 300 | 34 | 11.3% | 0.16 | 303.04 |
| code | 3 | 300 | 32 | 10.7% | 0.15 | 269.87 |
| code | 4 | 300 | 31 | 10.3% | 0.15 | 246.90 |
| code | 13 | 300 | 31 | 10.3% | 0.16 | 307.90 |
| code | 1 | 300 | 29 | 9.7% | 0.15 | 243.40 |
| code | 2 | 300 | 28 | 9.3% | 0.15 | 260.36 |

Math:

| kind | variant_id | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- |
| math | 7 | 300 | 107 | 35.7% | 0.36 | 149.88 |
| math | 10 | 300 | 105 | 35.0% | 0.35 | 153.38 |
| math | 4 | 300 | 100 | 33.3% | 0.33 | 121.88 |
| math | 18 | 300 | 100 | 33.3% | 0.33 | 207.01 |
| math | 16 | 300 | 99 | 33.0% | 0.33 | 185.72 |
| math | 6 | 300 | 98 | 32.7% | 0.33 | 143.18 |
| math | 13 | 300 | 94 | 31.3% | 0.31 | 182.22 |
| math | 17 | 300 | 94 | 31.3% | 0.31 | 199.61 |

## Weakest Prompt Variants

Code:

| kind | variant_id | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- |
| code | 10 | 300 | 19 | 6.3% | 0.11 | 276.57 |
| code | 6 | 300 | 23 | 7.7% | 0.12 | 273.37 |
| code | 7 | 300 | 23 | 7.7% | 0.12 | 272.34 |
| code | 9 | 300 | 23 | 7.7% | 0.12 | 299.54 |
| code | 5 | 300 | 24 | 8.0% | 0.13 | 263.86 |
| code | 11 | 300 | 25 | 8.3% | 0.13 | 293.86 |
| code | 14 | 300 | 25 | 8.3% | 0.14 | 324.86 |
| code | 16 | 300 | 25 | 8.3% | 0.12 | 311.40 |

Math:

| kind | variant_id | n | passed | pass_rate | mean_score | mean_prompt_tokens |
| --- | --- | --- | --- | --- | --- | --- |
| math | 2 | 300 | 81 | 27.0% | 0.27 | 132.27 |
| math | 8 | 300 | 83 | 27.7% | 0.28 | 164.11 |
| math | 3 | 300 | 85 | 28.3% | 0.28 | 139.68 |
| math | 14 | 300 | 85 | 28.3% | 0.28 | 196.11 |
| math | 5 | 300 | 87 | 29.0% | 0.29 | 135.77 |
| math | 15 | 300 | 89 | 29.7% | 0.30 | 203.51 |
| math | 1 | 300 | 93 | 31.0% | 0.31 | 118.38 |
| math | 9 | 300 | 93 | 31.0% | 0.31 | 171.18 |

## Token And Duration Correlations

Pearson correlations are computed against binary pass/fail and partial-credit score. Values near zero mean little linear relationship.

| kind | n | prompt_tokens_vs_passed | prompt_tokens_vs_score | completion_tokens_vs_passed | completion_tokens_vs_score | duration_vs_passed | duration_vs_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| code | 5400 | -0.01 | -0.02 | 0.00 | -0.00 | -0.02 | -0.02 |
| math | 5400 | -0.13 | -0.13 | 0.10 | 0.10 | 0.03 | 0.03 |

## Hardest Base Tasks

Code:

| kind | base_id | n | pass_rate | mean_score |
| --- | --- | --- | --- | --- |
| code | 2 | 108 | 0.0% | 0.00 |
| code | 4 | 108 | 0.0% | 0.00 |
| code | 43 | 108 | 0.0% | 0.00 |
| code | 44 | 108 | 0.0% | 0.00 |
| code | 48 | 108 | 0.0% | 0.00 |
| code | 49 | 108 | 0.0% | 0.00 |
| code | 9 | 108 | 0.0% | 0.00 |
| code | 35 | 108 | 0.0% | 0.00 |
| code | 40 | 108 | 0.0% | 0.00 |
| code | 38 | 108 | 0.0% | 0.00 |

Math:

| kind | base_id | n | pass_rate | mean_score |
| --- | --- | --- | --- | --- |
| math | math_048 | 108 | 0.0% | 0.00 |
| math | math_045 | 108 | 0.9% | 0.01 |
| math | math_039 | 108 | 2.8% | 0.03 |
| math | math_032 | 108 | 13.0% | 0.13 |
| math | math_004 | 108 | 13.9% | 0.14 |
| math | math_014 | 108 | 16.7% | 0.17 |
| math | math_015 | 108 | 16.7% | 0.17 |
| math | math_011 | 108 | 17.6% | 0.18 |
| math | math_033 | 108 | 17.6% | 0.18 |
| math | math_037 | 108 | 18.5% | 0.19 |

## Easiest Base Tasks

Code:

| kind | base_id | n | pass_rate | mean_score |
| --- | --- | --- | --- | --- |
| code | 45 | 108 | 48.1% | 0.62 |
| code | 11 | 108 | 38.9% | 0.39 |
| code | 39 | 108 | 35.2% | 0.44 |
| code | 15 | 108 | 31.5% | 0.33 |
| code | 46 | 108 | 31.5% | 0.32 |
| code | 8 | 108 | 28.7% | 0.39 |
| code | 17 | 108 | 28.7% | 0.30 |
| code | 30 | 108 | 25.0% | 0.26 |
| code | 21 | 108 | 22.2% | 0.31 |
| code | 16 | 108 | 20.4% | 0.41 |

Math:

| kind | base_id | n | pass_rate | mean_score |
| --- | --- | --- | --- | --- |
| math | math_029 | 108 | 86.1% | 0.86 |
| math | math_043 | 108 | 66.7% | 0.67 |
| math | math_005 | 108 | 53.7% | 0.54 |
| math | math_049 | 108 | 52.8% | 0.53 |
| math | math_025 | 108 | 52.8% | 0.53 |
| math | math_016 | 108 | 52.8% | 0.53 |
| math | math_042 | 108 | 51.9% | 0.52 |
| math | math_031 | 108 | 51.9% | 0.52 |
| math | math_040 | 108 | 50.0% | 0.50 |
| math | math_024 | 108 | 46.3% | 0.46 |

## Artifacts

- `summary_by_kind.csv`
- `summary_by_model.csv`
- `summary_by_model_and_kind.csv`
- `summary_by_variant.csv`
- `summary_by_model_variant.csv`
- `prompt_factor_summary.csv`
- `prompt_factor_contrasts.csv`
- `prompt_factor_interactions.csv`
- `prompt_factor_heterogeneity.csv`
- `model_factor_winners.csv`
- `model_kind_factor_differences.csv`
- `paired_fixed_effect_contrasts.csv`
- `behavior_summary.csv`
- `error_category_summary.csv`
- `dataset_shift_summary.csv`
- `token_outcome_correlations.csv`
- `base_task_summary.csv`
- `any_variant_summary.csv`
- `pass_rate_by_model.svg`
- `pass_rate_by_model_and_kind.svg`
- `important_insights_analysis.ipynb`
- `important_insights_analysis.executed.ipynb`
- `without_nemotron_analysis.ipynb`
- `without_nemotron_analysis.executed.ipynb`
