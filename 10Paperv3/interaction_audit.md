# Prompt-Factor and Factor-by-Model Interaction Audit

Generated from `prompt_framing_experiment_results.jsonl` (14,400 runs across 4 strata, clustered by 50 base tasks per stratum using Liang-Zeger CR1 cluster-robust sandwich covariance).

## 1. Joint Omnibus Tests of Two-Way Prompt-Factor Interactions (`Tone x Role`, `Tone x Format`, `Role x Format`)

| Stratum | N | Clusters | df | Wald chi2 | Wald F | p_joint |
|---|---:|---:|---:|---:|---:|---:|
| api code | 1800 | 50 | 8 | 3.62 | 0.45 | 0.8897 |
| api math | 1800 | 50 | 8 | 7.63 | 0.95 | 0.4707 |
| local code | 5400 | 50 | 8 | 14.79 | 1.85 | 0.0628 |
| local math | 5400 | 50 | 8 | 22.16 | 2.77 | 0.0048 |

- Minimum Benjamini-Hochberg FDR-adjusted q-value across all 32 two-way interaction terms: **0.1930**.
- Zero of 32 two-way prompt-factor interactions survive BH FDR correction within their 8-term stratum family or across all 32 terms.

## 2. Omnibus Wald Tests of Factor-by-Model Interactions (`Factor x Model`)

| Stratum | Interaction Block | df | Wald chi2 | Wald F | p_value |
|---|---|---:|---:|---:|---:|
| api code | All Factor x Model | 5 | 5.80 | 1.16 | 0.3255 |
| api code | Tone x Model | 2 | 4.22 | 2.11 | 0.1186 |
| api code | Role x Model | 1 | 0.50 | 0.50 | 0.4888 |
| api code | Format x Model | 2 | 2.44 | 1.22 | 0.2952 |
| api math | All Factor x Model | 5 | 9.03 | 1.81 | 0.1067 |
| api math | Tone x Model | 2 | 0.15 | 0.07 | 0.9196 |
| api math | Role x Model | 1 | 0.06 | 0.06 | 0.7972 |
| api math | Format x Model | 2 | 6.83 | 3.41 | 0.03213 |
| local code | All Factor x Model | 25 | 51.90 | 2.08 | 0.001273 |
| local code | Tone x Model | 10 | 8.56 | 0.86 | 0.5752 |
| local code | Role x Model | 5 | 4.65 | 0.93 | 0.4612 |
| local code | Format x Model | 10 | 9.12 | 0.91 | 0.5214 |
| local math | All Factor x Model | 25 | 91.68 | 3.67 | 2.547e-09 |
| local math | Tone x Model | 10 | 17.86 | 1.79 | 0.05712 |
| local math | Role x Model | 5 | 8.06 | 1.61 | 0.1516 |
| local math | Format x Model | 10 | 40.73 | 4.07 | 1.638e-05 |
