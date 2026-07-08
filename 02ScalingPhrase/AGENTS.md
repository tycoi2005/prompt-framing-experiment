# 02ScalingPhrase - Scaling Experiments

## OVERVIEW

Large-scale prompt framing experiments across API models (DeepSeek, Gemini) and local Ollama models. Includes remote execution, result merging, and comprehensive analysis.

## STRUCTURE

```
02ScalingPhrase/
├── apimodel/
│   ├── run_apis/               # API experiment runner + results
│   │   ├── run_api_matrix.py   # Main API runner
│   │   ├── deploy_and_run_remote.sh  # SSH deployment
│   │   └── results_final/      # Verified results
│   └── crafting_*/             # Problem generation
├── localmodel/
│   ├── *.ipynb                 # Jupyter notebooks
│   ├── problems/               # 900-row problem matrices
│   └── results/                # Local model results
├── results_analysis/           # Handoff package for thesis
│   ├── apimodels/              # API result JSONLs
│   ├── smallmodels/            # Local result JSONLs
│   └── prompt_templates/       # 18 framing variants
└── MathNet/                    # Math processing cache
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Run API experiments | `apimodel/run_apis/` | Uses remote SSH |
| Run local experiments | `localmodel/*.ipynb` | Ollama required |
| Analyze all results | `results_analysis/` | Thesis-ready package |
| Verify data integrity | `results_analysis/README.md` | 900 rows per file |

## CONVENTIONS

- Each result file: 900 rows (50 tasks × 18 prompt variants)
- Prompt variants: 18 framing combinations (tone × role × format)
- Results use `.jsonl` format with standardized fields
- `results_analysis/` is verified handoff package

## ANTI-PATTERNS

- Never modify `results_analysis/` directly (copy from sources)
- Never skip retry/error handling in API runners
- Never assume results are complete without row count verification
