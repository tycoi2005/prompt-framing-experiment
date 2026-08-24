# EMSE Submission Checklist — "Prompt Framing Sensitivity in LLMs for Code and Reasoning Tasks"

Target: *Empirical Software Engineering* (Springer, journal 10664), single-blind review.
Verified against official Springer pages (submission guidelines, ethics & disclosures, how-to-publish), 2026-07.

## Status legend
[x] done · [~] done but needs your input · [ ] to do before upload

## Manuscript package

- [x] Editable source files (mandatory): `report.tex` + `literature.bib` + `llncs.cls` + figure files. EMSE requires editable sources at every submission; LaTeX accepted (SN template recommended but plain formatting acceptable for initial submission).
- [x] References switched to **author-date** (`natbib` authoryear + `plainnat`), as EMSE requires. Reference list is alphabetized.
- [x] Abstract trimmed to ~225 words (EMSE: 150–250; structured abstract permitted but not required).
- [x] Keywords: 5 (EMSE: 4–6).
- [x] Figures embedded in the PDF at 300 dpi; **3a/3b split done** (see below). At acceptance, be ready to supply EPS/TIFF: line art ≥1200 dpi, halftones ≥300 dpi, Helvetica/Arial lettering, captions in the text file starting with bold "Fig. N".
- [x] Declarations exist in manuscript (Funding, Competing Interests, Data Availability, AI tools, Ethics).
- [x] **Separate title page** (`emse_title_page.tex` → `emse_title_page.pdf`): author block + Declarations section, with university email and ORCID filled in.
- [ ] Cover letter to the Editor: short note stating the submission is original, not under review elsewhere, and summarizing the contribution (also mention the replication package; EMSE values replicability).
- [ ] Enter funding info ("no specific funding") in Editorial Manager during submission (goes to CrossMark).
- [ ] Suggest 3–5 reviewers in the system (optional but usual; no one from UE to avoid COI).

## Notes on fit and likely reviewer concerns

- EMSE values replicability: the public repo + Kaggle dataset + regeneration scripts are a strength — cite them prominently (already in Data Availability + Replication Package sections).
- "Preference is given to studies that can be replicated or expanded upon" (aims & scope) — our replication package directly addresses this.
- Single-blind: no anonymization needed.
- LLM policy: LLM use documented in the manuscript (AI Tools Declaration + Methods) — done; AI-assisted copy editing need not be declared.
- No page limit; no submission fee. Hybrid OA optional (APC £2,390/$3,390) — standard (subscription) publication is free.
- Timeline targets: first decision usually < 3 months.

## Before upload — final self-check

1. `report.pdf` builds clean with author-date citations (done — see README build steps).
2. `emse_title_page.pdf` compiled, email + ORCID filled in.
3. Figures: Fig. 3a/3b referenced correctly in text (done).
4. Cover letter drafted (I can draft it when you're ready).
5. Zip of source files for upload: report.tex, literature.bib, llncs.cls, splncs03.bst (unused now — can omit), figures/*.png, emse_title_page.pdf.
