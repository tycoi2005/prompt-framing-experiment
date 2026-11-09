# Paper v3 (journal submission draft)

LLNCS-formatted journal draft: `report.tex` -> `report.pdf`.

## Analysis pipeline

All manuscript numbers are regenerated from
`02ScalingPhrase/results_analysis/prompt_framing_experiment_results.jsonl`
(14,400 runs) by the scripts in `scripts/`. Run from `scripts/`:

```bash
python3 recompute_manuscript_tables.py        # descriptive tables, behavior, mediation
python3 run_clustered_lpm_analysis.py         # clustered-LPM robustness check
python3 apply_multiple_comparison_correction.py  # Benjamini-Hochberg audit
python3 run_mixed_effects_analysis.py         # main inferential models + dominant-model
                                              # sensitivity + Nemotron task summary
python3 run_interaction_analysis.py           # two-way prompt-factor interactions +
                                              # factor-by-model omnibus Wald tests
```

Outputs land in `analysis/`:

- `clustered_lpm_prompt_effects.csv` — clustered-LPM contrasts per stratum
- `local_model_specific_bh.csv` — 60 local model-specific contrasts with BH q-values
- `mixed_effects_pass.csv` — main inferential results: logistic mixed-effects model
  (tone/role/format + model fixed effects, base-task random intercept, variational
  Bayes), per stratum, with odds ratios and AME in percentage points
- `mixed_effects_behavior.csv` — linear mixed models for log tokens/duration and
  logistic mixed model for result-only compliance
- `dominant_model_sensitivity.csv` — every prompt contrast re-estimated with and
  without the dominant model (Nemotron local, DeepSeek V4 Flash API), LPM and mixed
- `nemotron_task_solve_summary.csv` — per-task solve pattern across the 18 prompt
  conditions for the Nemotron 91.2% local-math result
- `two_way_factor_interactions.csv` — all 32 two-way prompt-factor interactions
  (`Tone x Role`, `Tone x Format`, `Role x Format`) with task-clustered SEs, 95% CIs,
  joint Wald tests, and within-stratum / global BH q-values
- `factor_by_model_interactions.csv` — omnibus Wald chi-square and F tests for
  `Factor x Model` interactions across all four strata

## Audits

- `claim_consistency_audit.md` — every abstract/discussion/conclusion claim mapped
  to a result-table cell; records the fixes required by reviewer feedback
- `mixed_effects_audit.md` — generated summary of the mixed-effects, dominant-model,
  and Nemotron analyses
- `nemotron_math_audit.md` — repository audit of the 91.2% local-math pass rate
- `interaction_audit.md` — generated summary of the two-way prompt-factor and
  factor-by-model interaction analyses

## Build

```bash
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

## Notes

- `improvement_plan.md` tracks the reviewer-feedback revision plan (9 points).
- The generated analysis CSVs are also mirrored in `../02ScalingPhrase/results_analysis/analysis/`.
- This folder supersedes `06Paperv2/` (removed in commit `95cf8b2`; recoverable
  from git history at `c0182f9`).
