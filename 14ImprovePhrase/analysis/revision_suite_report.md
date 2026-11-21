# Unified Revision Experiment Suite Report (`R1C4`, `R2C5/R2C14`, `R2C10`, `R2C7`)

## 1. `R1C4` — Measured Live End-to-End Pipeline (Real Retries)

| regime | model | policy | n | measured_r0_pct | measured_r1_pct | measured_r2_pct | gain_pp | init_parse_syntax_fail_pct | calls_per_1k | mean_total_comp_tok | mean_llm_s | mean_consumer_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| api | gemini-flash | neutral_plaintext | 50 | 68.00 | 74.00 | 74.00 | 6.00 | 0.00 | 1580.00 | 552.28 | 36.93 | 302.82 |
| api | gemini-flash | neutral_xml | 50 | 70.00 | 76.00 | 76.00 | 6.00 | 0.00 | 1540.00 | 563.96 | 30.39 | 285.03 |
| api | gemini-flash | polite_plaintext | 50 | 70.00 | 74.00 | 74.00 | 4.00 | 0.00 | 1560.00 | 571.24 | 34.44 | 65.61 |
| local | llama3.1-8b | neutral_plaintext | 50 | 18.00 | 28.00 | 32.00 | 14.00 | 2.00 | 2540.00 | 828.84 | 36.71 | 1257.85 |
| local | llama3.1-8b | neutral_xml | 50 | 10.00 | 18.00 | 22.00 | 12.00 | 0.00 | 2720.00 | 866.44 | 36.47 | 694.66 |
| local | llama3.1-8b | polite_plaintext | 50 | 12.00 | 14.00 | 20.00 | 8.00 | 2.00 | 2740.00 | 1074.34 | 44.57 | 821.81 |
| local | qwen2.5-7b | neutral_plaintext | 50 | 22.00 | 30.00 | 32.00 | 10.00 | 2.00 | 2480.00 | 611.18 | 26.86 | 1501.32 |
| local | qwen2.5-7b | neutral_xml | 50 | 18.00 | 30.00 | 30.00 | 12.00 | 2.00 | 2520.00 | 705.40 | 28.13 | 461.02 |
| local | qwen2.5-7b | polite_plaintext | 50 | 22.00 | 30.00 | 30.00 | 8.00 | 0.00 | 2480.00 | 675.80 | 26.99 | 1243.00 |

### Reference: Earlier Simulated Offline Replay (Clearly Separated)

| task_group | end_to_end_r0 | end_to_end_r1 | end_to_end_r2 | calls_per_1k_r2 |
| --- | --- | --- | --- | --- |
| Local code | 9.11 | 17.90 | 25.83 | 2729.92 |
| API Python | 67.83 | 89.71 | 96.71 | 1424.60 |

## 2. `R2C5 / R2C14` — Neutral Paraphrase & Length-Matched Neutral Controls

| regime | model_label | variant | n | pass_pct | mean_prompt_tok | mean_comp_tok | mean_llm_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| api | gemini-flash | neutral_length_matched | 30 | 66.67 | 251.90 | 369.40 | 3.67 |
| api | gemini-flash | neutral_paraphrase_short | 30 | 73.33 | 193.90 | 294.23 | 11.41 |
| local | llama3.1-8b | neutral_length_matched | 30 | 20.00 | 277.87 | 175.70 | 7.99 |
| local | llama3.1-8b | neutral_paraphrase_short | 30 | 20.00 | 219.87 | 327.43 | 13.79 |
| local | qwen2.5-7b | neutral_length_matched | 30 | 30.00 | 294.13 | 259.03 | 10.46 |
| local | qwen2.5-7b | neutral_paraphrase_short | 30 | 26.67 | 236.13 | 274.67 | 10.97 |

## 3. `R2C10` — Shared-Task Cross-Regime Comparison (Same TOANMATH Tasks)

| regime | model | policy | n | pass_pct | mean_comp_tok |
| --- | --- | --- | --- | --- | --- |
| API (shared TOANMATH) | gemini-flash | neutral_plaintext | 20 | 75.00 | 380.75 |
| API (shared TOANMATH) | gemini-flash | neutral_xml | 20 | 70.00 | 401.95 |
| API (shared TOANMATH) | gemini-flash | polite_plaintext | 20 | 65.00 | 378.00 |
| Local (reused TOANMATH) | deepseek-coder-6.7b-instruct | neutral_plaintext | 20 | 5.00 | 446.45 |
| Local (reused TOANMATH) | deepseek-coder-6.7b-instruct | neutral_xml | 20 | 5.00 | 439.35 |
| Local (reused TOANMATH) | deepseek-coder-6.7b-instruct | polite_plaintext | 20 | 0.00 | 461.30 |
| Local (reused TOANMATH) | gemma2-9b | neutral_plaintext | 20 | 15.00 | 167.25 |
| Local (reused TOANMATH) | gemma2-9b | neutral_xml | 20 | 20.00 | 168.35 |
| Local (reused TOANMATH) | gemma2-9b | polite_plaintext | 20 | 5.00 | 164.00 |
| Local (reused TOANMATH) | llama3.1-8b | neutral_plaintext | 20 | 15.00 | 326.90 |
| Local (reused TOANMATH) | llama3.1-8b | neutral_xml | 20 | 10.00 | 321.05 |
| Local (reused TOANMATH) | llama3.1-8b | polite_plaintext | 20 | 15.00 | 351.85 |
| Local (reused TOANMATH) | mistral-7b-instruct | neutral_plaintext | 20 | 0.00 | 334.90 |
| Local (reused TOANMATH) | mistral-7b-instruct | neutral_xml | 20 | 0.00 | 324.20 |
| Local (reused TOANMATH) | mistral-7b-instruct | polite_plaintext | 20 | 0.00 | 489.05 |
| Local (reused TOANMATH) | nemotron-3-nano-4b | neutral_plaintext | 20 | 20.00 | 1107.70 |
| Local (reused TOANMATH) | nemotron-3-nano-4b | neutral_xml | 20 | 30.00 | 1069.30 |
| Local (reused TOANMATH) | nemotron-3-nano-4b | polite_plaintext | 20 | 20.00 | 1112.45 |
| Local (reused TOANMATH) | qwen2.5-7b | neutral_plaintext | 20 | 20.00 | 259.25 |
| Local (reused TOANMATH) | qwen2.5-7b | neutral_xml | 20 | 30.00 | 285.15 |
| Local (reused TOANMATH) | qwen2.5-7b | polite_plaintext | 20 | 20.00 | 317.50 |

## 4. `R2C7` — Independent Non-Math SE Coding Benchmark (15 Tasks)

| regime | model_label | policy_label | n | pass_pct | mean_comp_tok | mean_llm_s |
| --- | --- | --- | --- | --- | --- | --- |
| api | gemini-flash | neutral_plaintext | 15 | 93.33 | 199.87 | 2.07 |
| api | gemini-flash | neutral_xml | 15 | 93.33 | 211.93 | 1.82 |
| api | gemini-flash | polite_plaintext | 15 | 93.33 | 248.87 | 2.86 |
| local | llama3.1-8b | neutral_plaintext | 15 | 40.00 | 195.00 | 8.66 |
| local | llama3.1-8b | neutral_xml | 15 | 53.33 | 238.13 | 10.34 |
| local | llama3.1-8b | polite_plaintext | 15 | 46.67 | 223.27 | 9.76 |
| local | qwen2.5-7b | neutral_plaintext | 15 | 46.67 | 152.20 | 6.56 |
| local | qwen2.5-7b | neutral_xml | 15 | 53.33 | 137.00 | 6.04 |
| local | qwen2.5-7b | polite_plaintext | 15 | 46.67 | 157.27 | 6.76 |
