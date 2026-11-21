# Replication Package Recursive Audit (`R2M5`)

- **Audited directory:** `/Users/macos/LearningSpace/ue-courses/Thesis/09PublicRepo`
- **Total non-`.git` directories:** 60
- **Total non-`.git` files:** 1364
- **Top-level entries:** `.gitignore`, `01PilotPhrase/`, `02ScalingPhrase/`, `10Paperv3/`, `14ImprovePhrase/`, `README.md`

## 1. Legacy Thesis Directory / File Check

- **Matches for `thesis` / `03Thesis` / `04Thesis` anywhere in tree:** **0**
  - None found (clean).

## 2. Secret / Credential File Check

- **Matches for `.env*` / `.key` / `.pem`:** **0**
  - None found (clean).

## 3. Mentions of `thesis` in `09PublicRepo/README.md`

- None.

## 4. Data Availability Statement Excerpt (`13Submission_v1/LLM_Prompt_Framing_R00_updated.tex`)

```latex
\section{Data Availability Statement}\label{data-availability-statement}

The complete, self-contained replication package—comprising the 18-variant factorial prompt templates (\texttt{02ScalingPhrase/results\_analysis/prompt\_templates/}), local (Tesla P100 primary and Tesla T4 $k=3$) and cloud API (Google Generative Language API, Pioneer AI primary, and AI/ML API $k=3$) evaluation runners, the consolidated $14{,}400$-run primary JSONL dataset, the $14{,}398$-run $k = 3$ repeated-generation dataset (\texttt{14ImprovePhrase/results\_*\_repeated/}), the $450$-workflow live end-to-end retry pipeline logs, the $180$ neutral paraphrase/length-matched controls, the $20$-task shared-regime comparison, the $15$-task non-math SE coding benchmark (\texttt{14ImprovePhrase/results\_revision/}), reproducible statistical analysis scripts mirrored in both \texttt{02ScalingPhrase/results\_analysis/scripts/} and \texttt{10Paperv3/scripts/} (mixed-effects, clustered LPM, two-way interactions, BH-FDR, behavioral adjustment, variance decomposition, power analysis, and dominant-model sensitivity), and the 200-task oracle, compliance, and recursive repository audit logs (\texttt{14ImprovePhrase/analysi
```
