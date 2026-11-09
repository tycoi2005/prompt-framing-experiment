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

The `02ScalingPhrase/results_analysis/` and `10Paperv3/scripts/` directories contain the pre-aggregated 14,400-run JSONL dataset and the Python scripts used to generate all descriptive tables, mixed-effects logistic/linear models, clustered LPM robustness checks, Benjamini–Hochberg FDR adjustments, post-treatment behavioral adjustments, and dominant-model leave-one-out sensitivity checks reported in the paper:

```bash
cd 10Paperv3/scripts
python3 recompute_manuscript_tables.py
python3 run_clustered_lpm_analysis.py
python3 apply_multiple_comparison_correction.py
python3 run_mixed_effects_analysis.py
python3 run_interaction_analysis.py
python3 characterize_task_datasets.py
python3 run_variance_decomposition.py
python3 run_effect_size_summary.py
```

## License & Data Availability

All prompt templates, evaluation scripts, analysis notebooks, and aggregated result datasets are publicly available.
