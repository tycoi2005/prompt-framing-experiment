#!/usr/bin/env python3
"""Recursive audit of the public replication package (09PublicRepo) for R2M5.

Checks:
  1. Recursively scans 09PublicRepo/ for any legacy thesis directories/files
     (03Thesis, 03Thesis_draft, 04Thesis_final, *thesis*), secrets (.env, .env.json),
     or unexplained top-level artifacts.
  2. Inspects 09PublicRepo/README.md and the Data Availability Statement in
     13Submission_v1/LLM_Prompt_Framing_R00_updated.tex for consistency.

Writes:
  - 14ImprovePhrase/analysis/replication_package_audit.md
"""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PUB_DIR = REPO_ROOT / "09PublicRepo" if (REPO_ROOT / "09PublicRepo").exists() else REPO_ROOT
MANUSCRIPT_TEX = (
    REPO_ROOT / "13Submission_v1" / "LLM_Prompt_Framing_R00_updated.tex"
    if (REPO_ROOT / "13Submission_v1" / "LLM_Prompt_Framing_R00_updated.tex").exists()
    else PUB_DIR / "10Paperv3" / "LLM_Prompt_Framing_R00_updated.tex"
)
OUT_MD = SCRIPT_DIR / "analysis" / "replication_package_audit.md"


def main() -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    if not PUB_DIR.exists():
        OUT_MD.write_text("# Replication Package Audit (R2M5)\n\n`09PublicRepo/` does not exist.\n", encoding="utf-8")
        print("09PublicRepo does not exist.")
        return

    all_paths = [p for p in PUB_DIR.rglob("*") if ".git" not in p.parts]
    dirs = [p for p in all_paths if p.is_dir()]
    files = [p for p in all_paths if p.is_file()]

    thesis_hits = [
        str(p.relative_to(PUB_DIR))
        for p in all_paths
        if any(k in p.name.lower() for k in ("thesis", "03thesis", "04thesis"))
    ]
    secret_hits = [
        str(p.relative_to(PUB_DIR))
        for p in files
        if p.name.startswith(".env") or p.suffix == ".pem" or p.suffix == ".key"
    ]
    top_level = sorted(p.name + ("/" if p.is_dir() else "") for p in PUB_DIR.iterdir() if p.name != ".git")

    # Check Data Availability Statement in manuscript
    das_excerpt = ""
    if MANUSCRIPT_TEX.exists():
        tex = MANUSCRIPT_TEX.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(\\section\{Data Availability Statement\}.*?)(?:\\section|\\subsection|\\bibliographystyle|\Z)", tex, re.S | re.I)
        if m:
            das_excerpt = m.group(1).strip()[:1200]

    # Check if 09PublicRepo/README.md mentions thesis
    readme_thesis_mentions = []
    readme_path = PUB_DIR / "README.md"
    if readme_path.exists():
        for i, ln in enumerate(readme_path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if "thesis" in ln.lower():
                readme_thesis_mentions.append(f"L{i}: {ln.strip()}")

    md = [
        "# Replication Package Recursive Audit (`R2M5`)",
        "",
        f"- **Audited directory:** `{PUB_DIR}`",
        f"- **Total non-`.git` directories:** {len(dirs)}",
        f"- **Total non-`.git` files:** {len(files)}",
        f"- **Top-level entries:** {', '.join(f'`{x}`' for x in top_level)}",
        "",
        "## 1. Legacy Thesis Directory / File Check",
        "",
        f"- **Matches for `thesis` / `03Thesis` / `04Thesis` anywhere in tree:** **{len(thesis_hits)}**",
        *(["  - `" + h + "`" for h in thesis_hits] if thesis_hits else ["  - None found (clean)."]),
        "",
        "## 2. Secret / Credential File Check",
        "",
        f"- **Matches for `.env*` / `.key` / `.pem`:** **{len(secret_hits)}**",
        *(["  - `" + h + "`" for h in secret_hits] if secret_hits else ["  - None found (clean)."]),
        "",
        "## 3. Mentions of `thesis` in `09PublicRepo/README.md`",
        "",
        *(["- " + m for m in readme_thesis_mentions] if readme_thesis_mentions else ["- None."]),
        "",
        "## 4. Data Availability Statement Excerpt (`13Submission_v1/LLM_Prompt_Framing_R00_updated.tex`)",
        "",
        "```latex",
        das_excerpt or "(Not found)",
        "```",
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {OUT_MD}\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
