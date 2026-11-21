# Independent Repeated Generations (k = 3) Summary

Total valid runs loaded: **14398** across **8** model(s) and **4** stratum/strata.

## 1. Within-Cell Variability

| stratum | model | n_runs | n_cells_multi | mean_k | overall_pass_pct | rep_pass_sd_pp | within_cell_flip_pct | exact_agreement_pct | mean_within_cell_sd_pp | mean_tok_within_sd | mean_dur_within_sd_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API Python | deepseek-v4-flash-aimlapi | 900 | 300 | 3.00 | 39.67 | 2.08 | 23.67 | 76.33 | 28.09 | 155.17 | 1.15 |
| API Python | gemini-flash | 900 | 300 | 3.00 | 68.33 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 16.46 |
| API math | deepseek-v4-flash-aimlapi | 900 | 300 | 3.00 | 80.11 | 0.51 | 15.00 | 85.00 | 22.36 | 135.76 | 0.72 |
| API math | gemini-flash | 900 | 300 | 3.00 | 23.67 | 0.00 | 0.00 | 100.00 | 0.00 | 0.00 | 5.00 |
| Local Python | deepseek-coder-6.7b-instruct | 899 | 300 | 3.00 | 3.00 | 0.58 | 5.00 | 95.00 | 12.91 | 86.86 | 2.94 |
| Local Python | gemma2-9b | 900 | 300 | 3.00 | 13.89 | 0.51 | 7.00 | 93.00 | 15.28 | 16.24 | 0.71 |
| Local Python | llama3.1-8b | 900 | 300 | 3.00 | 8.78 | 0.69 | 12.67 | 87.33 | 20.55 | 59.77 | 1.83 |
| Local Python | mistral-7b-instruct | 900 | 300 | 3.00 | 1.00 | 0.88 | 2.33 | 97.67 | 8.82 | 66.79 | 2.26 |
| Local Python | nemotron-3-nano-4b | 900 | 300 | 3.00 | 17.11 | 0.38 | 20.00 | 80.00 | 25.82 | 258.10 | 5.47 |
| Local Python | qwen2.5-7b | 900 | 300 | 3.00 | 18.33 | 1.33 | 12.00 | 88.00 | 20.00 | 36.48 | 1.44 |
| Local math | deepseek-coder-6.7b-instruct | 899 | 300 | 3.00 | 4.78 | 0.52 | 10.67 | 89.33 | 18.86 | 89.95 | 2.84 |
| Local math | gemma2-9b | 900 | 300 | 3.00 | 17.56 | 0.19 | 2.67 | 97.33 | 9.43 | 0.43 | 0.02 |
| Local math | llama3.1-8b | 900 | 300 | 3.00 | 48.22 | 0.51 | 28.33 | 71.67 | 30.73 | 87.16 | 2.40 |
| Local math | mistral-7b-instruct | 900 | 300 | 3.00 | 9.33 | 1.00 | 10.00 | 90.00 | 18.26 | 26.59 | 0.83 |
| Local math | nemotron-3-nano-4b | 900 | 300 | 3.00 | 90.56 | 0.19 | 4.33 | 95.67 | 12.02 | 49.46 | 1.00 |
| Local math | qwen2.5-7b | 900 | 300 | 3.00 | 24.00 | 0.33 | 4.00 | 96.00 | 11.55 | 0.39 | 0.02 |

## 2. Prompt Contrasts (k = 3 vs. Single-Repetition k = 1)

| stratum | contrast | category_id | n_tasks | diff_k3_pp | se_k3_pp | ci_low_k3_pp | ci_high_k3_pp | mde80_k3_pp | diff_rep1_pp | se_rep1_pp | mde80_rep1_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API Python | JSON vs plaintext | 2 | 50 | 0.33 | 2.50 | -4.56 | 5.23 | 7.00 | -2.00 | 3.18 | 8.91 |
| API Python | XML vs plaintext | 3 | 50 | 1.67 | 3.10 | -4.40 | 7.73 | 8.67 | 0.00 | 3.50 | 9.80 |
| API Python | Role vs no role | 4 | 50 | 0.33 | 3.18 | -5.89 | 6.56 | 8.90 | 0.00 | 4.29 | 12.01 |
| API Python | Polite vs neutral | 7 | 50 | -3.00 | 3.18 | -9.24 | 3.24 | 8.92 | -4.00 | 4.70 | 13.18 |
| API Python | Aggressive vs neutral | 13 | 50 | -3.33 | 3.27 | -9.73 | 3.06 | 9.15 | -1.00 | 3.91 | 10.95 |
| API math | JSON vs plaintext | 2 | 50 | 1.33 | 1.42 | -1.44 | 4.11 | 3.97 | 1.00 | 1.74 | 4.88 |
| API math | XML vs plaintext | 3 | 50 | 1.33 | 2.28 | -3.13 | 5.79 | 6.38 | 0.00 | 3.19 | 8.95 |
| API math | Role vs no role | 4 | 50 | -0.33 | 2.05 | -4.35 | 3.68 | 5.74 | -2.00 | 3.18 | 8.91 |
| API math | Polite vs neutral | 7 | 50 | 0.33 | 2.16 | -3.89 | 4.56 | 6.04 | -2.00 | 2.84 | 7.96 |
| API math | Aggressive vs neutral | 13 | 50 | 0.67 | 1.58 | -2.42 | 3.76 | 4.42 | 4.00 | 2.41 | 6.75 |
| Local Python | JSON vs plaintext | 2 | 50 | -0.22 | 1.09 | -2.35 | 1.91 | 3.05 | 0.33 | 1.54 | 4.32 |
| Local Python | XML vs plaintext | 3 | 50 | -0.11 | 1.38 | -2.81 | 2.59 | 3.86 | 0.33 | 1.39 | 3.89 |
| Local Python | Role vs no role | 4 | 50 | -1.44 | 1.11 | -3.62 | 0.73 | 3.11 | -0.33 | 1.75 | 4.90 |
| Local Python | Polite vs neutral | 7 | 50 | -2.56 | 1.17 | -4.85 | -0.27 | 3.27 | -3.00 | 1.23 | 3.45 |
| Local Python | Aggressive vs neutral | 13 | 50 | -1.56 | 1.12 | -3.76 | 0.65 | 3.15 | -2.33 | 1.43 | 4.00 |
| Local math | JSON vs plaintext | 2 | 50 | -6.78 | 1.40 | -9.53 | -4.03 | 3.94 | -7.33 | 1.79 | 5.02 |
| Local math | XML vs plaintext | 3 | 50 | -1.67 | 1.18 | -3.98 | 0.65 | 3.31 | -2.00 | 1.55 | 4.35 |
| Local math | Role vs no role | 4 | 50 | -0.67 | 1.22 | -3.05 | 1.72 | 3.40 | -0.67 | 1.58 | 4.42 |
| Local math | Polite vs neutral | 7 | 50 | 0.11 | 1.07 | -1.99 | 2.21 | 3.00 | -1.33 | 1.71 | 4.78 |
| Local math | Aggressive vs neutral | 13 | 50 | -1.86 | 1.16 | -4.14 | 0.42 | 3.26 | -3.67 | 1.60 | 4.48 |
