# Results Final Analysis

## Overall

| Model | Total | Passed | Failed | Accuracy | API errors | Empty responses | Leading-zero eval errors | Unresolved response issues | Total tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | 1800 | 1340 | 460 | 74.444% | 0 | 4 | 0 | 4 | 2578502 |
| gemini-flash | 1800 | 838 | 962 | 46.556% | 0 | 0 | 0 | 0 | 706410 |

## By Dataset

| Model | Dataset | Total | Passed | Failed | Accuracy | API errors | Empty responses | Leading-zero eval errors | Avg s | Median s | Total tokens |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash | math | 900 | 741 | 159 | 82.333% | 0 | 1 | 0 | 18.438 | 9.405 | 1160814 |
| deepseek-v4-flash | python | 900 | 599 | 301 | 66.556% | 0 | 3 | 0 | 22.012 | 16.117 | 1417688 |
| gemini-flash | math | 900 | 217 | 683 | 24.111% | 0 | 0 | 0 | 10.205 | 3.397 | 165678 |
| gemini-flash | python | 900 | 621 | 279 | 69.000% | 0 | 0 | 0 | 17.968 | 10.296 | 540732 |

## Pairwise Comparison

| Dataset | Model A | Model B | Rows | Both pass | A only | B only | Both fail |
|---|---|---|---:|---:|---:|---:|---:|
| math | deepseek-v4-flash | gemini-flash | 900 | 200 | 541 | 17 | 142 |
| python | deepseek-v4-flash | gemini-flash | 900 | 499 | 100 | 122 | 179 |
