# Prompt Framing Experiment - Replication Package

This repository contains the full replication package for the research paper: **"Prompt Framing Sensitivity in Large Language Models for Code and Reasoning Tasks"**.

## Directory Structure

* `01PilotPhrase/`: Contains the pilot study phase, including prompt generation scripts and initial evaluations.
* `02ScalingPhrase/`: The core scaling experiments containing:
  * `apimodel/`: Scripts for running API-based models.
  * `localmodel/`: Jupyter notebooks and scripts for evaluating local Ollama models.
  * `results_analysis/`: Statistical notebooks, aggregated result JSONL files, extraction scripts, and the final analysis report (`report.md`).
* `10Paperv3/`: The empirical paper source code (LNCS format, `report.tex`), scripts, analysis datasets, and generated figures.
* `12Thesisv4/`: The modular Master's Thesis LaTeX source code (`thesis.tex`, `chapters/`, `misc/`, `bib/`, `figures/`).

## Prerequisites

To fully replicate the experiments, you may need:
1. **Python 3.x**: Ensure `pip` is installed. Check the respective directories for `requirements.txt` files.
2. **Ollama**: Required for running the local model experiments. Ensure the Ollama service is running (`ollama serve`) before executing those notebooks.
3. **API Keys**: To run the API models in `02ScalingPhrase/apimodel/`, you must provide your own API keys via `.env` files (these have been intentionally excluded from this repository).
4. **LaTeX**: A standard TeX distribution (e.g., TeX Live, MiKTeX) is needed to compile the documents in `10Paperv3/` and `12Thesisv4/`.

## Compiling the Documents

### 1. Compiling the Paper (`10Paperv3`)
```bash
cd 10Paperv3
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

### 2. Compiling the Thesis (`12Thesisv4`)
```bash
cd 12Thesisv4
pdflatex -interaction=nonstopmode -halt-on-error thesis.tex
bibtex thesis
makeglossaries thesis
pdflatex -interaction=nonstopmode -halt-on-error thesis.tex
pdflatex -interaction=nonstopmode -halt-on-error thesis.tex
```

## Running the Analysis

The `02ScalingPhrase/results_analysis/` folder contains pre-aggregated JSONL results and the corresponding Jupyter notebooks used to generate the tables and figures for the manuscript. You can re-run these notebooks to independently verify the statistical outputs and visualizations.

## License & Data Availability

All prompt templates, evaluation scripts, analysis notebooks, and aggregated result datasets are publicly available.
