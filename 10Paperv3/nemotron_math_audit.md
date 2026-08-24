# Nemotron Math Data-Integrity Audit

Date: 2026-06-25.

This note summarizes the repository audit for the unusually high Nemotron local
math pass rate reported in Paper v2.

## Scope

Audited file:

- `02ScalingPhrase/results_analysis/smallmodels/nemotron-3-nano-4b_1_50.math.jsonl`

Reason:

- Nemotron 3 Nano 4B reached `821 / 900 = 91.2%` on local math, far above the
  other local models.

## Checks Completed

Current recomputation from the JSONL file shows:

| Check | Result |
|---|---:|
| Rows | 900 |
| Unique task ids | 900 |
| Duplicate task ids | 0 |
| Unique base tasks | 50 |
| Unique prompt variants | 18 |
| Base-task balance | every base task has 18 variants |
| Variant balance | every prompt variant has 50 base tasks |
| Stored passes | 821 / 900 |
| Independent pass recomputation | 821 / 900 |
| Recomputed/stored pass mismatches | 0 |
| Prompt-variant pass-count range | 44-47 / 50 |
| Base tasks solved under all 18 variants | 42 / 50 |

The prompt-variant pass-count distribution is:

| Passes per variant | Number of variants |
|---:|---:|
| 44 | 3 |
| 45 | 3 |
| 46 | 10 |
| 47 | 2 |

## Interpretation

The audit found no row-level data-integrity issue explaining the 91.2% pass
rate. The result is unusual but internally consistent with the stored result
file, prompt-matrix balance, and numeric evaluator output.

Important caveat: the math result file stores normalized final-answer text in
`response_text`, not necessarily the full raw model response. Token counts still
reflect the raw model response, but this JSONL cannot fully support a manual
audit of original formatting, ambiguity, or visible solution work. The paper
should therefore describe Nemotron's result as final-answer correctness under
the numeric evaluator, not as proof that every original response was
unambiguous or well-formed.
