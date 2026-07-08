# API Results Analysis Report

Analyzed `3600` rows from `02ScalingPhrase/apimodel/run_apis/results_final`.

## Model By Dataset
- `deepseek-v4-flash` / `math`: 742/900 passed (82.444%), unresolved issues `0`.
- `deepseek-v4-flash` / `python`: 600/900 passed (66.667%), unresolved issues `0`.
- `gemini-flash` / `math`: 217/900 passed (24.111%), unresolved issues `0`.
- `gemini-flash` / `python`: 621/900 passed (69.0%), unresolved issues `0`.

## Overall By Model
- `deepseek-v4-flash`: 1342/1800 passed (74.556%), total tokens `2578987`.
- `gemini-flash`: 838/1800 passed (46.556%), total tokens `706410`.

## Pairwise Common-Task Comparison
- `math` `deepseek-v4-flash` vs `gemini-flash`: both pass `200`, deepseek-v4-flash only `542`, gemini-flash only `17`, both fail `141`.
- `python` `deepseek-v4-flash` vs `gemini-flash`: both pass `500`, deepseek-v4-flash only `100`, gemini-flash only `121`, both fail `179`.

## Artifacts
- `summary_by_model.csv`
- `summary_by_model_dataset.csv`
- `summary_by_category.csv`
- `model_comparison.csv`
- `analysis_summary.json`
- `api_prompt_factor_summary.csv`
- `api_prompt_factor_significance.csv`
- `important_insights_analysis.executed.ipynb`
