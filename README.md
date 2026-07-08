# Prompt Framing Experiment - Replication Package

This repository contains the full replication package for the research paper: **"Prompt Framing Sensitivity in Large Language Models for Code and Reasoning Tasks"**.

## Directory Structure

* `01PilotPhrase/`: Contains the pilot study phase, including prompt generation scripts and initial evaluations.
* `02ScalingPhrase/`: The core scaling experiments containing:
  * `apimodel/`: Scripts for running API-based models.
  * `localmodel/`: Jupyter notebooks and scripts for evaluating local Ollama models.
  * `results_analysis/`: Statistical notebooks, aggregated result JSONL files, extraction scripts, and the final analysis report (`report.md`).
* `03Thesis/`: The LaTeX source code and compilation materials for the monolithic master thesis document (`main.tex`).
* `06Paperv2/`: The condensed paper draft and summary derived from the thesis.

## Prerequisites

To fully replicate the experiments, you may need:
1. **Python 3.x**: Ensure `pip` is installed. Check the respective directories for `requirements.txt` files.
2. **Ollama**: Required for running the local model experiments. Ensure the Ollama service is running (`ollama serve`) before executing those notebooks.
3. **API Keys**: To run the API models in `02ScalingPhrase/apimodel/`, you must provide your own API keys via `.env` files (these have been intentionally excluded from this repository).
4. **LaTeX**: A standard TeX distribution (e.g., TeX Live, MiKTeX) is needed to compile the documents in `03Thesis/` and `06Paperv2/`.

## Compiling the Documents

To compile the thesis:
```bash
cd 03Thesis
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

## Running the Analysis

The `02ScalingPhrase/results_analysis/` folder contains pre-aggregated JSONL results and the corresponding Jupyter notebooks used to generate the tables and figures for the manuscript. You can re-run these notebooks to independently verify the statistical outputs and visualizations.

## License & Data Availability

All prompt templates, evaluation scripts, analysis notebooks, and aggregated result datasets are publicly available.
