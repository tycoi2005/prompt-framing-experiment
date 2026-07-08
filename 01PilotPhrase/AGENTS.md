# 01PilotPhrase - LLM Framing Pilot Study

## OVERVIEW

Python pipeline for testing LLM performance under different prompt framing conditions (tone, pressure, role-playing). Generates prompt matrices, evaluates models, and analyzes results.

## STRUCTURE

```
01PilotPhrase/
├── generate_prompt_matrix.py    # Create prompt variations
├── generate_dataset.py          # Parse/translate VN math problems
├── evaluate_mbpp.py             # Run LLM evaluation
├── verify_all.py                # Validate datasets
├── data/                        # CSV files (problems, matrices)
├── problems/                    # JSON problem sets
├── checkpoints/                 # Evaluation results (.jsonl)
├── logs/                        # Execution logs
└── pivot_problem_dataset/       # Dataset utilities
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Generate prompts | `generate_prompt_matrix.py` | Uses `data/problems.csv` |
| Run evaluation | `evaluate_mbpp.py` | Supports resume, dry-run |
| View results | `checkpoints/*.jsonl` | Date/model organized |
| Add problems | `data/problems.csv` | CSV format |

## CONVENTIONS

- `.env` required: `API_BASE`, `API_KEY`, `MODEL`
- Results in `checkpoints/` are resumable
- Use `verify_all.py` before analysis

## ANTI-PATTERNS

- Never skip completed task IDs during resume
- Never mix prose with structured output
- Never leave dead code or unused imports
