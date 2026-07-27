# Mixed-Effects Analysis Audit

Main inferential model: logistic mixed-effects model for pass/fail with
tone/role/format fixed effects, model fixed effects, and a random intercept
per base task with one shared variance (BinomialBayesMixedGLM, variational
Bayes), fitted per stratum. AME = average marginal effect in percentage
points, averaged over the observed covariates and the estimated task
random-intercept distribution; intervals from posterior draws. LPM
contrasts remain as interpretability layer.

## Pass/fail: logistic mixed-effects results

| Stratum | Contrast | OR [95% int] | AME pp [95% int] | p |
|---|---|---:|---:|---:|
| API Python | Aggressive tone | 1.05 [0.83, 1.34] | +0.6 [-2.3, +3.4] | 0.686 |
| API Python | Polite tone | 1.05 [0.83, 1.34] | +0.6 [-2.2, +3.4] | 0.686 |
| API Python | Role framing | 0.92 [0.76, 1.11] | -1.1 [-3.5, +1.2] | 0.381 |
| API Python | JSON wrapper | 1.32 [1.04, 1.68] | +3.4 [+0.5, +6.2] | 0.022 |
| API Python | XML wrapper | 1.55 [1.21, 1.97] | +5.2 [+2.4, +8.0] | <0.001 |
| API math | Aggressive tone | 1.05 [0.81, 1.38] | +0.5 [-2.1, +2.9] | 0.697 |
| API math | Polite tone | 0.91 [0.70, 1.18] | -0.9 [-3.5, +1.5] | 0.476 |
| API math | Role framing | 0.74 [0.60, 0.92] | -2.8 [-4.8, -0.8] | 0.006 |
| API math | JSON wrapper | 0.87 [0.67, 1.14] | -1.3 [-3.8, +1.2] | 0.325 |
| API math | XML wrapper | 0.78 [0.60, 1.02] | -2.3 [-4.7, +0.1] | 0.069 |
| Local code | Aggressive tone | 0.98 [0.80, 1.20] | -0.1 [-1.0, +0.9] | 0.858 |
| Local code | Polite tone | 0.89 [0.72, 1.09] | -0.5 [-1.4, +0.4] | 0.265 |
| Local code | Role framing | 0.81 [0.68, 0.96] | -1.0 [-1.7, -0.2] | 0.013 |
| Local code | JSON wrapper | 1.01 [0.83, 1.24] | +0.1 [-0.8, +1.0] | 0.900 |
| Local code | XML wrapper | 1.15 [0.94, 1.41] | +0.7 [-0.2, +1.6] | 0.164 |
| Local math | Aggressive tone | 1.11 [0.95, 1.29] | +0.9 [-0.5, +2.2] | 0.198 |
| Local math | Polite tone | 1.20 [1.03, 1.40] | +1.6 [+0.3, +3.0] | 0.019 |
| Local math | Role framing | 1.28 [1.13, 1.45] | +2.1 [+1.1, +3.2] | <0.001 |
| Local math | JSON wrapper | 0.62 [0.52, 0.72] | -4.1 [-5.3, -2.8] | <0.001 |
| Local math | XML wrapper | 0.78 [0.66, 0.91] | -2.1 [-3.4, -0.9] | 0.001 |

## Behavioral outcomes: mixed models

| Stratum | Outcome | Contrast | Effect | p |
|---|---|---|---:|---:|
| API Python | log_completion_tokens | Aggressive tone | +14.20 % | <0.001 |
| API Python | log_completion_tokens | Polite tone | +6.49 % | 0.059 |
| API Python | log_completion_tokens | Role framing | -1.53 % | 0.587 |
| API Python | log_completion_tokens | JSON wrapper | -6.50 % | 0.059 |
| API Python | log_completion_tokens | XML wrapper | -5.24 % | 0.128 |
| API Python | log_duration | Aggressive tone | +2.35 % | 0.609 |
| API Python | log_duration | Polite tone | +1.06 % | 0.817 |
| API Python | log_duration | Role framing | -6.09 % | 0.105 |
| API Python | log_duration | JSON wrapper | -4.45 % | 0.333 |
| API Python | log_duration | XML wrapper | -4.45 % | 0.333 |
| API Python | result_only | Aggressive tone | +nan pp (AME) | nan |
| API Python | result_only | Polite tone | +nan pp (AME) | nan |
| API Python | result_only | Role framing | +nan pp (AME) | nan |
| API Python | result_only | JSON wrapper | +nan pp (AME) | nan |
| API Python | result_only | XML wrapper | +nan pp (AME) | nan |
| API math | log_completion_tokens | Aggressive tone | +12.78 % | 0.097 |
| API math | log_completion_tokens | Polite tone | +1.18 % | 0.878 |
| API math | log_completion_tokens | Role framing | +2.80 % | 0.656 |
| API math | log_completion_tokens | JSON wrapper | -5.20 % | 0.500 |
| API math | log_completion_tokens | XML wrapper | -17.52 % | 0.023 |
| API math | log_duration | Aggressive tone | +0.73 % | 0.902 |
| API math | log_duration | Polite tone | -1.99 % | 0.736 |
| API math | log_duration | Role framing | -1.06 % | 0.825 |
| API math | log_duration | JSON wrapper | -10.71 % | 0.069 |
| API math | log_duration | XML wrapper | -9.76 % | 0.097 |
| API math | result_only | Aggressive tone | +0.82 pp (AME) | 0.401 |
| API math | result_only | Polite tone | +1.99 pp (AME) | 0.054 |
| API math | result_only | Role framing | -3.85 pp (AME) | <0.001 |
| API math | result_only | JSON wrapper | +5.78 pp (AME) | <0.001 |
| API math | result_only | XML wrapper | +5.12 pp (AME) | <0.001 |
| Local code | log_completion_tokens | Aggressive tone | +0.55 % | 0.678 |
| Local code | log_completion_tokens | Polite tone | +12.40 % | <0.001 |
| Local code | log_completion_tokens | Role framing | +3.17 % | 0.003 |
| Local code | log_completion_tokens | JSON wrapper | -3.46 % | 0.009 |
| Local code | log_completion_tokens | XML wrapper | -4.10 % | 0.002 |
| Local code | log_duration | Aggressive tone | +0.52 % | 0.639 |
| Local code | log_duration | Polite tone | +10.76 % | <0.001 |
| Local code | log_duration | Role framing | +2.41 % | 0.008 |
| Local code | log_duration | JSON wrapper | -3.32 % | 0.003 |
| Local code | log_duration | XML wrapper | -3.57 % | 0.001 |
| Local code | result_only | Aggressive tone | -1.48 pp (AME) | 0.005 |
| Local code | result_only | Polite tone | -7.05 pp (AME) | <0.001 |
| Local code | result_only | Role framing | -1.18 pp (AME) | 0.005 |
| Local code | result_only | JSON wrapper | +4.30 pp (AME) | <0.001 |
| Local code | result_only | XML wrapper | +6.98 pp (AME) | <0.001 |
| Local math | log_completion_tokens | Aggressive tone | +4.39 % | 0.087 |
| Local math | log_completion_tokens | Polite tone | +10.97 % | <0.001 |
| Local math | log_completion_tokens | Role framing | +8.86 % | <0.001 |
| Local math | log_completion_tokens | JSON wrapper | -19.80 % | <0.001 |
| Local math | log_completion_tokens | XML wrapper | -1.96 % | 0.445 |
| Local math | log_duration | Aggressive tone | +4.24 % | 0.004 |
| Local math | log_duration | Polite tone | +7.51 % | <0.001 |
| Local math | log_duration | Role framing | +3.98 % | <0.001 |
| Local math | log_duration | JSON wrapper | -11.16 % | <0.001 |
| Local math | log_duration | XML wrapper | -1.14 % | 0.438 |
| Local math | result_only | Aggressive tone | -1.47 pp (AME) | 0.003 |
| Local math | result_only | Polite tone | -1.36 pp (AME) | 0.005 |
| Local math | result_only | Role framing | -1.09 pp (AME) | 0.007 |
| Local math | result_only | JSON wrapper | +0.74 pp (AME) | 0.135 |
| Local math | result_only | XML wrapper | -0.36 pp (AME) | 0.457 |

## Dominant-model sensitivity (prompt effects, full panel vs leave-one-out)

| Stratum | Contrast | Panel | LPM pp | Mixed AME pp | Mixed OR |
|---|---|---|---:|---:|---:|
| API Python | Aggressive tone | full panel | +0.5 | +0.6 | 1.05 |
| API Python | Polite tone | full panel | +0.5 | +0.5 | 1.05 |
| API Python | Role framing | full panel | -1.0 | -1.0 | 0.92 |
| API Python | JSON wrapper | full panel | +3.2 | +3.4 | 1.32 |
| API Python | XML wrapper | full panel | +4.8 | +5.3 | 1.55 |
| API Python | Aggressive tone | without DeepSeek V4 Flash | -2.7 | -2.7 | 0.71 |
| API Python | Polite tone | without DeepSeek V4 Flash | -2.3 | -2.3 | 0.75 |
| API Python | Role framing | without DeepSeek V4 Flash | -2.0 | -2.1 | 0.77 |
| API Python | JSON wrapper | without DeepSeek V4 Flash | +1.3 | +1.6 | 1.22 |
| API Python | XML wrapper | without DeepSeek V4 Flash | +2.7 | +3.1 | 1.48 |
| API math | Aggressive tone | full panel | +0.3 | +0.5 | 1.05 |
| API math | Polite tone | full panel | -1.0 | -0.9 | 0.91 |
| API math | Role framing | full panel | -2.8 | -2.8 | 0.74 |
| API math | JSON wrapper | full panel | -1.3 | -1.3 | 0.87 |
| API math | XML wrapper | full panel | -2.3 | -2.3 | 0.78 |
| API math | Aggressive tone | without DeepSeek V4 Flash | +0.7 | +0.7 | 1.14 |
| API math | Polite tone | without DeepSeek V4 Flash | -1.3 | -2.5 | 0.58 |
| API math | Role framing | without DeepSeek V4 Flash | -2.4 | -4.1 | 0.42 |
| API math | JSON wrapper | without DeepSeek V4 Flash | -3.7 | -6.1 | 0.26 |
| API math | XML wrapper | without DeepSeek V4 Flash | -0.0 | -0.2 | 0.94 |
| Local code | Aggressive tone | full panel | -0.0 | -0.1 | 0.98 |
| Local code | Polite tone | full panel | -0.5 | -0.5 | 0.89 |
| Local code | Role framing | full panel | -1.0 | -1.0 | 0.81 |
| Local code | JSON wrapper | full panel | +0.2 | +0.1 | 1.01 |
| Local code | XML wrapper | full panel | +0.8 | +0.7 | 1.15 |
| Local code | Aggressive tone | without Nemotron 3 Nano | -0.1 | -0.1 | 0.96 |
| Local code | Polite tone | without Nemotron 3 Nano | -0.6 | -0.6 | 0.84 |
| Local code | Role framing | without Nemotron 3 Nano | -0.9 | -0.9 | 0.79 |
| Local code | JSON wrapper | without Nemotron 3 Nano | +0.1 | -0.0 | 0.99 |
| Local code | XML wrapper | without Nemotron 3 Nano | +0.3 | +0.1 | 1.04 |
| Local math | Aggressive tone | full panel | +0.9 | +0.9 | 1.11 |
| Local math | Polite tone | full panel | +1.7 | +1.6 | 1.20 |
| Local math | Role framing | full panel | +2.2 | +2.1 | 1.28 |
| Local math | JSON wrapper | full panel | -4.2 | -4.1 | 0.62 |
| Local math | XML wrapper | full panel | -2.2 | -2.1 | 0.78 |
| Local math | Aggressive tone | without Nemotron 3 Nano | +1.3 | +1.2 | 1.13 |
| Local math | Polite tone | without Nemotron 3 Nano | +2.3 | +2.3 | 1.26 |
| Local math | Role framing | without Nemotron 3 Nano | +2.4 | +2.3 | 1.28 |
| Local math | JSON wrapper | without Nemotron 3 Nano | -5.3 | -5.2 | 0.57 |
| Local math | XML wrapper | without Nemotron 3 Nano | -2.5 | -2.4 | 0.77 |

## Nemotron 3 Nano local math: task-level solve summary (50 tasks x 18 variants)

- solved under all 18 conditions: 42
- solved under some conditions: 6
- solved under no condition: 2
