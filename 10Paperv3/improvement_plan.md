# Improvement Plan — Journal Paper (10Paperv3) → then Thesis (07Thesisv2)

**Source:** Prof. Iftikhar Ahmed's feedback (2026-07-20), 9 points + P.S.
**Strategy decided:** Paper first, then port improvements back into the thesis.
**Key context:**
- Current paper: `10Paperv3/report.tex` (Springer LNCS, ~1000 lines). Mixed-effects are described in §3.3 as a "consideration" but **not yet actually fitted** — this is the core gap behind feedback point 1.
- Full dataset: `02ScalingPhrase/results_analysis/prompt_framing_experiment_results.jsonl` (14,400 runs, 27 MB).
- The deleted `06Paperv2/` scripts and audits are recoverable from git (`git show HEAD:06Paperv2/...`) and should be reused, not rewritten from scratch.
- `statsmodels 0.14.4` + `pandas` are already available — no new dependencies needed.
- No new experiments required; the 14,400-run dataset is sufficient (professor confirmed).

---

## Phase 0 — Setup and recovery

- [x] Recover reusable assets from git history into `10Paperv3/`:
  - `git show HEAD:06Paperv2/scripts/recompute_manuscript_tables.py` → adapt as base for new analysis scripts
  - `git show HEAD:06Paperv2/scripts/run_clustered_lpm_analysis.py`
  - `git show HEAD:06Paperv2/claim_consistency_audit.md` → template for the Phase 4 audit
- [x] Create `10Paperv3/scripts/` and `10Paperv3/analysis/` directories; all new numbers go through reproducible scripts, never hand-computed into the text.

---

## Phase 1 — New analyses (produce the numbers everything else depends on)

### 1. Mixed-effects analysis as main inferential basis *(feedback point 1)*
- [x] New script: `10Paperv3/scripts/run_mixed_effects_analysis.py`
  - Outcome: binary pass/fail → **logistic mixed-effects model** (statsmodels `BinomialBayesMixedGLM`)
  - Random intercept for **base task** (the repeated-measures unit); model as fixed effect (or crossed random intercepts for task + model if estimation is stable)
  - Fit per stratum: local code, local math, API code, API math — matching the paper's existing stratification
  - Predictors: tone, role, format factors vs. baseline (neutral / no role / plain text)
  - Report: odds ratios + 95% CIs, **plus average marginal effects in percentage points** so the tables stay interpretable next to the existing contrasts
  - Behavioral outcomes (log tokens, log duration): linear mixed models with same random structure
- [x] Paper edits:
  - §3.3 "Fixed-Effect and Mixed-Effect Considerations" → rewrite: mixed-effects logistic is now the **main inferential model**; LPM percentage-point contrasts remain as the interpretability layer; clustered-SE LPMs remain as robustness checks
  - §4 Results: add mixed-effects table(s); update narrative where conclusions change
- [x] **Verify:** every headline effect that the mixed model weakens or reverses gets flagged for the Phase 4 claim audit

### 2. Dominant-model sensitivity of *prompt effects* (feedback point 3)
- [x] Extend the analysis beyond "overall average changes": re-estimate the **main tone, role, and format contrasts** (percentage points + the new mixed model) with and without Nemotron, and with and without DeepSeek V4 Flash
- [x] Deliverable table: effect direction and magnitude, full panel vs. leave-one-dominant-out panel, per stratum
- [x] Paper edits: rewrite §3.7 "Dominant-Model Sensitivity" and its results subsection so it directly supports the "pooled averages are dangerous" argument

### 3. Nemotron 91.2% local math transparency (feedback point 6)
- [x] Task-level summary from the JSONL: of the 50 math tasks, how many were solved under **all 18** prompt conditions, **some**, or **none**
- [x] Add a small table + one short paragraph next to the existing Nemotron audit; keep the audit, this complements it

---

## Phase 2 — Interpretation and framing edits (depend on Phase 1 numbers)

### 4. Mediation / behavioral-control language (feedback point 2)
- [x] Sweep `report.tex` for causal phrasing: `caused by`, `due to`, `explains`, `drives`, `mechanism`, `cognitive process`
- [x] Standard replacements:
  - "the coefficient is **attenuated after adjustment** for measured behavioral variables"
  - "these behaviors are **associated with part of the observed contrast**"
- [x] §3.6 already has the post-treatment caveat — propagate that exact caution into the abstract, results, discussion, and conclusion so wording is consistent everywhere

### 5. Local vs. API as complementary experiments (feedback point 4)
- [x] Add explicit framing in §2 (Design) and §4 (Results intro): different models, task datasets, serving environments, execution settings → **complementary experiments, not head-to-head comparisons**
- [x] Sweep for any sentence attributing local-vs-API performance differences to model ability alone; add the confound caveat (serving infra, decoding defaults, datasets)

### 6. Code-task representativeness (feedback point 8)
- [x] Add a paragraph in §2.4 (Tasks) + a Limitations sentence: math-derived Python problems were chosen for **automatic verifiability and clean factor isolation**; the study evaluates **controlled initial code generation**, not repository-level, multi-file, or iterative software development

---

## Phase 3 — Positioning

### 7. Related Work gap table (feedback point 7)
- [x] Identify the 6–8 closest prior studies from `literature.bib` (+ targeted additions if gaps)
- [x] Compact comparison table, columns: multiple models · tone · role framing · prompt format · coding tasks · reasoning tasks · behavioral metrics · factorial design · reproducibility
- [x] Rewrite §1.5 "Research Gap" around the table: state directly what this paper contributes beyond each close study

---

## Phase 4 — Consistency audit (after all numbers are final)

### 8. Abstract and headline claims (feedback point 5)
- [x] Known fixes:
  - Abstract: structured-format benefit belongs to **API Python**, not "cloud models with math tasks"
  - Replace "**context length**" with "**completion tokens**" everywhere that is the reported measure
- [x] Full audit: extract **every** numerical and qualitative claim in abstract, discussion, conclusion; map each to a specific result-table cell; fix or delete any that don't match. Use the recovered `claim_consistency_audit.md` as the working document, regenerated against the Phase 1 numbers.

---

## Phase 5 — Language and concision (last, on frozen content)

### 9. Polish (feedback point 9)
- [x] Shorten Discussion and practical-recommendation sections: each argument appears **once**, in one canonical place; cut repeated explanations
- [x] Grammar/awkwardness pass over the whole manuscript
- [x] Final full read-through for journal-paper register (not thesis-chapter register)

---

## Phase 6 — Port to thesis + verification

- [x] Port the improved sections (mixed-effects strategy/results, mediation wording, sensitivity, related-work table, task-representativeness paragraph, corrected claims) from `10Paperv3/report.tex` into `07Thesisv2/main.tex`
- [x] Regenerate any thesis tables/figures from the new analysis CSVs
- [x] Rebuild both PDFs (`pdflatex` × 2 + `bibtex`/`biber` as configured) and confirm clean compiles
- [x] Re-run the claim audit one final time against the thesis version

---

## Suggested order rationale

Phase 1 first because every later phase depends on the final numbers. Phase 4 (claim audit) must come after the numbers freeze. Phase 5 (language) comes last so polish isn't wasted on text that later changes. Estimated effort: Phase 1 is the largest chunk (new modeling + tables); Phases 2–4 are focused editing passes; Phase 5 is a full-manuscript pass.

## Response to the P.S.

Professor asked about submission status → reply that thesis submission is planned, and these revisions target the journal paper first, with improvements ported back into the thesis before submission (per the "both, paper first" decision).
