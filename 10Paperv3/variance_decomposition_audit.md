# Model vs. Prompt Effects: Variance Decomposition and Formal Tests

Generated from `prompt_framing_experiment_results.jsonl` (14,400 runs). Bootstrap: 2000 task-cluster resamples, seed 20260514.

## Variance decomposition of Pass@1 (eta-squared, % of total SS) and repeated-measures F-tests

| Stratum | Component | df | eta^2 (%) | Error term | F | p |
|---|---|---:|---:|---|---:|---:|
| Local code | model | 5 | 7.22 | model_x_task | 11.89 | 2.61e-10 |
| Local code | task | 49 | 19.65 |  |  |  |
| Local code | prompt | 17 | 0.27 | task_x_prompt | 1.93 | 0.013 |
| Local code | tone | 2 | 0.01 | tone_x_task | 0.28 | 0.757 |
| Local code | role | 1 | 0.03 | role_x_task | 5.04 | 0.0293 |
| Local code | format | 2 | 0.02 | format_x_task | 0.73 | 0.482 |
| Local code | prompt_interactions | 12 | 0.21 |  |  |  |
| Local code | model_x_task | 245 | 29.77 |  |  |  |
| Local code | model_x_prompt | 85 | 0.55 | residual | 0.75 | 0.959 |
| Local code | task_x_prompt | 833 | 6.80 |  |  |  |
| Local code | residual | 4165 | 35.74 |  |  |  |
| Local math | model | 5 | 40.97 | model_x_task | 91.49 | 5.03e-54 |
| Local math | task | 49 | 12.78 |  |  |  |
| Local math | prompt | 17 | 0.27 | task_x_prompt | 3.52 | 2.03e-06 |
| Local math | tone | 2 | 0.02 | tone_x_task | 2.54 | 0.0844 |
| Local math | role | 1 | 0.06 | role_x_task | 9.93 | 0.00277 |
| Local math | format | 2 | 0.14 | format_x_task | 7.85 | 0.000689 |
| Local math | prompt_interactions | 12 | 0.05 |  |  |  |
| Local math | model_x_task | 245 | 21.94 |  |  |  |
| Local math | model_x_prompt | 85 | 0.84 | residual | 2.12 | 1.58e-08 |
| Local math | task_x_prompt | 833 | 3.71 |  |  |  |
| Local math | residual | 4165 | 19.50 |  |  |  |
| API Python | model | 1 | 0.06 | model_x_task | 0.43 | 0.515 |
| API Python | task | 49 | 50.13 |  |  |  |
| API Python | prompt | 17 | 0.29 | task_x_prompt | 0.65 | 0.849 |
| API Python | tone | 2 | 0.00 | tone_x_task | 0.04 | 0.959 |
| API Python | role | 1 | 0.01 | role_x_task | 0.51 | 0.478 |
| API Python | format | 2 | 0.18 | format_x_task | 3.99 | 0.0216 |
| API Python | prompt_interactions | 12 | 0.09 |  |  |  |
| API Python | model_x_task | 49 | 7.10 |  |  |  |
| API Python | model_x_prompt | 17 | 0.43 | residual | 1.02 | 0.429 |
| API Python | task_x_prompt | 833 | 21.45 |  |  |  |
| API Python | residual | 833 | 20.54 |  |  |  |
| API math | model | 1 | 34.17 | model_x_task | 119.70 | 9.35e-15 |
| API math | task | 49 | 23.80 |  |  |  |
| API math | prompt | 17 | 0.41 | task_x_prompt | 1.48 | 0.0942 |
| API math | tone | 2 | 0.01 | tone_x_task | 0.49 | 0.614 |
| API math | role | 1 | 0.08 | role_x_task | 4.36 | 0.042 |
| API math | format | 2 | 0.04 | format_x_task | 1.18 | 0.312 |
| API math | prompt_interactions | 12 | 0.28 |  |  |  |
| API math | model_x_task | 49 | 13.99 |  |  |  |
| API math | model_x_prompt | 17 | 0.43 | residual | 1.54 | 0.0733 |
| API math | task_x_prompt | 833 | 13.41 |  |  |  |
| API math | residual | 833 | 13.78 |  |  |  |

## Model vs. prompt comparison

| Stratum | Model range (pp) | Prompt-variant range (pp) | eta^2 model [95% CI] | eta^2 prompt [95% CI] | Diff (pp) 95% CI | Ratio median [95% CI] | Boot p (model<=prompt) | LPM Wald model chi2(df), p | LPM Wald prompt chi2(df), p | Latent share model / prompt (%) |
|---|---:|---:|---|---|---|---|---:|---|---|---|
| Local code | 22.3 | 5.3 | 7.22 [4.45, 11.27] | 0.27 [0.22, 0.67] | [4.07, 10.83] | 19.3 [9.9, 33.4] | 0.0000 | 26.7(5), 6.64e-05 | 5.8(5), 0.331 | 40.36 / 0.14 |
| Local math | 85.6 | 8.7 | 40.97 [33.06, 50.59] | 0.27 [0.19, 0.55] | [32.57, 50.27] | 122.9 [73.7, 226.2] | 0.0000 | 546.1(5), 9.01e-116 | 30.6(5), 1.12e-05 | 47.35 / 0.46 |
| API Python | 2.3 | 10.0 | 0.06 [0.00, 1.08] | 0.29 [0.27, 1.42] | [-1.31, 0.39] | 0.2 [0.0, 1.7] | 0.9135 | 0.4(1), 0.513 | 8.9(5), 0.114 | 0.09 / 0.27 |
| API math | 58.3 | 11.0 | 34.17 [23.52, 47.00] | 0.41 [0.33, 1.13] | [22.90, 46.35] | 52.8 [27.2, 109.2] | 0.0000 | 119.3(1), 8.98e-28 | 7.1(5), 0.212 | 35.57 / 0.23 |
