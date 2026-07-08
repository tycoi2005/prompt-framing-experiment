# Results Final Analysis

## Overall

| Model | Total | Passed | Failed | Accuracy | API errors | Empty responses | Leading-zero eval errors | Unresolved response issues | Total tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | 1800 | 1337 | 463 | 74.278% | 0 | 11 | 0 | 11 | 2566328 |
| gemini-flash | 1800 | 838 | 962 | 46.556% | 0 | 0 | 0 | 0 | 706410 |

## By Dataset

| Model | Dataset | Total | Passed | Failed | Accuracy | API errors | Empty responses | Leading-zero eval errors | Avg s | Median s | Total tokens |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | math | 900 | 740 | 160 | 82.222% | 0 | 2 | 0 | 18.377 | 9.418 | 1160409 |
| deepseek-v4-flash | python | 900 | 597 | 303 | 66.333% | 0 | 9 | 0 | 21.696 | 16.117 | 1405919 |
| gemini-flash | math | 900 | 217 | 683 | 24.111% | 0 | 0 | 0 | 10.205 | 3.397 | 165678 |
| gemini-flash | python | 900 | 621 | 279 | 69.000% | 0 | 0 | 0 | 17.968 | 10.296 | 540732 |

## Pairwise Comparison

| Dataset | Model A | Model B | Rows | Both pass | A only | B only | Both fail |
|---|---|---|---:|---:|---:|---:|---:|
| math | deepseek-v4-flash | gemini-flash | 900 | 200 | 540 | 17 | 143 |
| python | deepseek-v4-flash | gemini-flash | 900 | 498 | 99 | 123 | 180 |

## Outputs
- `summary_by_model_dataset.csv`
- `summary_by_model.csv`
- `summary_by_category.csv`
- `model_comparison.csv`
- `analysis_summary.json`
