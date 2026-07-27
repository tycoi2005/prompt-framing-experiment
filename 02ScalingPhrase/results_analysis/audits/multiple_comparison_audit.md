# Multiple-Comparison Audit

This audit applies Benjamini-Hochberg false-discovery-rate correction to the local model-specific baseline contrasts from `02ScalingPhrase/localmodel/results/analysis/prompt_factor_contrasts.csv`. The source table compares prompt levels against the experiment baselines: neutral tone, no role, and plaintext format.

## Families

| Family | Contrasts | Uncorrected p < 0.05 | BH q <= 0.05 |
|---|---:|---:|---:|
| All local model-specific baseline contrasts | 60 | 7 | 2 |
| Local code baseline contrasts | 30 | 1 | 0 |
| Local math baseline contrasts | 30 | 6 | 3 |

## Significant After BH Across All 60 Local Contrasts

| Kind | Model | Factor | Level | Diff | p | BH q |
|---|---|---|---|---:|---:|---:|
| math | llama3.1-8b_1_50 | format | json | -15.667 pp | 0.000110156346326 | 0.00660938077959 |
| math | qwen2.5-7b_1_50 | role_binary | role | 10.222 pp | 0.000302199242225 | 0.00906597726675 |

## Significant After BH Within The Local Math Family

| Kind | Model | Factor | Level | Diff | p | BH q |
|---|---|---|---|---:|---:|---:|
| math | llama3.1-8b_1_50 | format | json | -15.667 pp | 0.000110156346326 | 0.00330469038979 |
| math | qwen2.5-7b_1_50 | role_binary | role | 10.222 pp | 0.000302199242225 | 0.00453298863337 |
| math | deepseek-coder-6.7b-instruct_1_50 | format | xml | -5.667 pp | 0.00391218209513 | 0.0391218209513 |

## Interpretation

The correction supports the manuscript's cautious interpretation. Local code has no model-specific baseline contrast that remains significant after task-kind-level BH correction. Local math retains the strongest heterogeneous effects: Llama 3.1 loses performance under JSON, Qwen 2.5 gains from role framing, and DeepSeek Coder loses performance under XML when correction is applied within the math family. If all local model-specific baseline contrasts are treated as one family, only the Llama JSON and Qwen role effects remain significant.
