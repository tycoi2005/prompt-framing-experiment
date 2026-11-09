# Prompt Framing Experiment - Replication Package

This repository contains the full replication package for the research paper: **"Prompt Framing Sensitivity in Large Language Models for Code and Reasoning Tasks"**.

## Directory Structure

* `01PilotPhrase/`: Contains the pilot study phase, including prompt generation scripts (`generate_prompt_matrix.py`) and initial MBPP evaluations (`evaluate_mbpp.py`).
* `02ScalingPhrase/`: The core scaling experiments containing:
  * `apimodel/`: Scripts and prompt-matrix runners for evaluating hosted cloud API models (`gemini-flash`, `deepseek-v4-flash`).
  * `localmodel/`: Jupyter notebooks and evaluation runners for local Ollama models (`qwen2.5-7b`, `llama3.1-8b`, `gemma2-9b`, `deepseek-coder-6.7b`, `mistral-7b-instruct`, `nemotron-3-nano-4b`).
  * `results_analysis/`: Consolidated 14,400-run JSONL dataset (`prompt_framing_experiment_results.jsonl`), statistical scripts, audit reports, and analysis notebooks.
* `10Paperv3/`: The empirical manuscript source code (`report.tex`), reproducible statistical analysis pipeline (`scripts/`), generated CSV tables (`analysis/`), audit reports, and figures (`figures/`).

## Prerequisites

To fully replicate the experiments, you may need:
1. **Python 3.x**: Ensure `pip` is installed. Check the respective directories for `requirements.txt` files.
2. **Ollama**: Required for running the local model experiments (`v0.20.0` used in the paper). Ensure the Ollama service is running (`ollama serve`) before executing those notebooks.
3. **API Keys**: To run the API models in `02ScalingPhrase/apimodel/`, you must provide your own API keys via `.env` files (these have been intentionally excluded from this repository).
4. **LaTeX**: A standard TeX distribution (e.g., TeX Live, MiKTeX) is needed to compile the manuscript in `10Paperv3/`.

## Compiling the Manuscript (`10Paperv3`)

```bash
cd 10Paperv3
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

## Running the Reproducible Statistical Pipeline

The `02ScalingPhrase/results_analysis/` and `10Paperv3/scripts/` directories contain the pre-aggregated 14,400-run JSONL dataset and the Python scripts used to generate every number in the paper: descriptive tables, mixed-effects logistic/linear models, clustered LPM robustness checks, Benjamini–Hochberg FDR adjustments, post-treatment behavioral adjustments, dominant-model leave-one-out sensitivity, two-way interaction tests, formal model-vs-prompt variance decomposition, effect-size reporting, task characterization, design-based power/MDE analysis, single-run noise floors, and the end-to-end parser/retry replay. Run from `10Paperv3/scripts`:

```bash
cd 10Paperv3/scripts
python3 recompute_manuscript_tables.py           # descriptive tables, behavior, mediation
python3 run_clustered_lpm_analysis.py            # clustered-LPM robustness check
python3 apply_multiple_comparison_correction.py   # Benjamini-Hochberg audit
python3 run_mixed_effects_analysis.py            # main inferential models + dominant-model
                                                 # sensitivity + Nemotron task summary
python3 run_interaction_analysis.py              # two-way prompt-factor interactions +
                                                 # factor-by-model omnibus Wald tests
python3 characterize_task_datasets.py            # quantitative characterization of the
                                                 # four 50-task evaluation benchmarks
python3 run_variance_decomposition.py            # formal model-vs-prompt comparison
python3 run_effect_size_summary.py               # consolidated effect-size ledger
python3 run_api_behavior_adjustment.py           # RQ4 behavioral adjustment for the API strata
python3 run_power_analysis.py                    # design-based power analysis (MDE at 80/90%)
python3 run_single_run_noise.py                  # single-run Bernoulli noise floor vs clustered SE
python3 run_pipeline_replay.py                   # offline end-to-end replay: strict parser +
                                                 # reformat-retry policy
python3 make_figures.py                          # manuscript figures, including the labelled,
                                                 # 95%-CI behavior panels
```

The `02ScalingPhrase/results_analysis/scripts/` directory mirrors the same scripts for readers who start from the raw experiment tree.

## License & Data Availability

All prompt templates, evaluation scripts, analysis notebooks, and aggregated result datasets are publicly available.
