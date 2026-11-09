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
python3 characterize_task_datasets.py         # quantitative characterization of the
                                              # four 50-task evaluation benchmarks
python3 run_variance_decomposition.py         # formal model-vs-prompt comparison
                                              # (eta^2, RM F-tests, bootstrap, logit)
python3 run_effect_size_summary.py            # consolidated Section 4.8 effect-size
                                              # ledger (reads existing CSVs only)
python3 run_api_behavior_adjustment.py        # RQ4 behavioral adjustment for the API
                                              # strata + API Python compliance audit
python3 run_power_analysis.py                 # design-based power analysis (MDE at
                                              # 80/90% power, task ICC, design effect)
python3 run_single_run_noise.py               # single-run Bernoulli noise floor vs.
                                              # realized clustered SEs
python3 run_pipeline_replay.py                # offline end-to-end replay: strict
                                              # parser + reformat-retry policy
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
- `task_dataset_characterization.csv` — summary statistics across all four 50-task
  benchmarks (statement length, arity/givens, reference LOC/SLOC, AST nodes, McCabe
  cyclomatic complexity, topic/difficulty breakdown, and pass-rate distributions)
- `per_task_characterization.csv` — task-level metrics across all 200 base tasks
- `model_vs_prompt_variance_decomposition.csv` — balanced ANOVA decomposition of
  Pass@1 (model, task, prompt, tone/role/format, interactions) with eta-squared
  shares and repeated-measures F-tests (task as random block)
- `model_vs_prompt_formal_tests.csv` — task-cluster bootstrap CIs for the model vs.
  prompt eta-squared difference/ratio, clustered LPM block Wald tests, and
  latent-scale (logit) variance shares
- `effect_size_summary.csv` — consolidated Section 4.8 effect-size ledger
  (Pass@1 AMEs/ORs, behavior effects, attenuation percentages, eta-squared
  shares, and model-specific contrasts) with the source CSV for every row
- `manuscript_api_mediation.csv` — RQ4 behavioral-adjustment decomposition for the
  two API strata (total vs. token/compliance/duration-adjusted contrasts, with
  attenuation and the joint-control specification per stratum)
- `manuscript_api_compliance_summary.csv` — audit of API Python code-only
  compliance recovered from the executed candidate program (1,799/1,800 = 99.9%,
  i.e. ceiling, which is why that stratum's joint adjustment omits the control)
- `manuscript_power_analysis.csv` — per-contrast power ledger for all 20
  stratum × contrast cells: task-clustered and i.i.d. SEs, design effect,
  effective sample size, MDE at 80%/90% power, achieved power, and the base
  tasks required to detect a 1 pp or 2 pp contrast
- `manuscript_power_summary.csv` — stratum-level power summary (ICC, design-effect
  range, clustered SE range, MDE range, task-count extrapolations) used for
  Table 18 of the manuscript
- `manuscript_single_run_noise.csv` — per-contrast single-run Bernoulli noise
  floor versus the realized task-clustered SE, with the MDE under a doubled
  within-cell variance (Section 7.4)
- `manuscript_single_run_noise_models.csv` — per model–task cell: pass rate,
  Bernoulli floor, and the resulting 80% MDE range
- `manuscript_pipeline_replay.csv` — offline replay of all 14,400 responses
  through a strict parser and 0/1/2 reformat-retry policies, per stratum and
  per prompt level, with expected calls and added latency (Table 19)

## Audits

- `claim_consistency_audit.md` — every abstract/discussion/conclusion claim mapped
  to a result-table cell; records the fixes required by reviewer feedback
- `mixed_effects_audit.md` — generated summary of the mixed-effects, dominant-model,
  and Nemotron analyses
- `nemotron_math_audit.md` — repository audit of the 91.2% local-math pass rate
- `interaction_audit.md` — generated summary of the two-way prompt-factor and
  factor-by-model interaction analyses
- `task_dataset_audit.md` — generated summary of the four 50-task evaluation suites
- `variance_decomposition_audit.md` — generated summary of the formal model-vs-prompt
  comparison
- `effect_size_audit.md` — generated ledger for Section 4.8, mapping every headline
  effect size to its source CSV and documenting the descriptive cross-check

## Build

```bash
pdflatex -interaction=nonstopmode -halt-on-error report.tex
bibtex report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

## Notes

- `improvement_plan.md` tracks the reviewer-feedback revision plan (9 points).
- The thesis version of these analyses lives in `../07Thesisv2/`; the same analysis
  CSVs are mirrored in `../07Thesisv2/analysis/`.
- This folder supersedes `06Paperv2/` (removed in commit `95cf8b2`; recoverable
  from git history at `c0182f9`).
