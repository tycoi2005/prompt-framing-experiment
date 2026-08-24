# Clustered Linear-Probability Robustness Audit

Source data: `02ScalingPhrase/results_analysis/prompt_framing_experiment_results.jsonl`.

Each model is an OLS linear-probability model for pass/fail outcome with prompt factors and model fixed effects. Standard errors are clustered by base task. Models are fitted separately for local code, local math, API Python, and API math.

## Selected Results

| Group | Contrast | Coeff. | Cluster SE | p |
|---|---|---:|---:|---:|
| API Python | JSON vs plaintext | +3.17 pp | 1.73 pp | 0.068 |
| API Python | XML vs plaintext | +4.83 pp | 1.77 pp | 0.006 |
| API math | role vs none | -2.78 pp | 1.33 pp | 0.037 |
| Local code | role vs none | -1.04 pp | 0.46 pp | 0.025 |
| Local math | polite vs neutral | +1.67 pp | 0.79 pp | 0.035 |
| Local math | role vs none | +2.19 pp | 0.69 pp | 0.002 |
| Local math | JSON vs plaintext | -4.17 pp | 1.11 pp | <0.001 |
| Local math | XML vs plaintext | -2.22 pp | 1.02 pp | 0.030 |

## Interpretation

The clustered analysis preserves the main direction of the headline pass-rate effects while changing some uncertainty estimates. API Python XML remains significant, while API Python JSON becomes marginal. Local math JSON, XML, role framing, and polite tone are significant with task-clustered standard errors. A small local-code role penalty also appears, but its magnitude is about one percentage point and should be interpreted cautiously because the paper treats clustered LPMs as robustness checks rather than final causal estimates.
