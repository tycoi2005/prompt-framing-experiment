"""Convert crawled VietJack On vao 10 math questions to the local math JSON shape."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


INPUT_CSV = Path("vietjack_onvao10_2026/questions.csv")
OUTPUT_JSON = Path("VietJack_OnVao10_2026.math.json")
SKIPPED_CSV = Path("VietJack_OnVao10_2026.skipped.csv")


def clean_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def option_label(option_text: str, fallback_index: int) -> str:
    match = re.match(r"\s*([A-D])\s*[.)]", option_text or "", flags=re.I)
    if match:
        return match.group(1).upper()
    return chr(ord("A") + fallback_index)


def build_multiple_choice_prompt(row: dict[str, str]) -> tuple[str, str]:
    answers = json.loads(row.get("answers_json") or "[]")
    option_lines: list[str] = []
    correct: list[str] = []

    for index, answer in enumerate(answers):
        text = clean_text(answer.get("content_text", ""))
        label = option_label(text, index)
        option_lines.append(text if text else f"{label}.")
        if str(answer.get("answer", "")).upper() == "Y":
            correct.append(label)

    prompt_parts = [
        clean_text(row["content_text"]),
        "",
        "Options:",
        *option_lines,
        "",
        "Choose the correct option letter.",
    ]
    return "\n".join(prompt_parts).strip(), ", ".join(correct)


def build_essay_prompt(row: dict[str, str]) -> tuple[str, str]:
    return clean_text(row["content_text"]), clean_text(row["reason_text"])


def convert() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    with INPUT_CSV.open(newline="", encoding="utf-8") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=1):
            if row["question_type"] == "test":
                prompt, expected_answer = build_multiple_choice_prompt(row)
            else:
                prompt, expected_answer = build_essay_prompt(row)

            if not expected_answer.strip():
                skipped.append(
                    {
                        "source_number": str(number),
                        "question_id": row["question_id"],
                        "exam_id": row["exam_id"],
                        "question_type": row["question_type"],
                        "test_title": row["test_title"],
                    }
                )
                continue

            tasks.append(
                {
                    "id": f"vietjack_math_{len(tasks) + 1:04d}",
                    "category": "math",
                    "difficulty": "medium",
                    "prompt": prompt,
                    "expected_answer": expected_answer,
                    "source_task_id": int(row["question_id"]),
                    "source_old_id": int(row["exam_id"]),
                }
            )
    with SKIPPED_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "source_number",
            "question_id",
            "exam_id",
            "question_type",
            "test_title",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(skipped)
    return tasks


def main() -> None:
    tasks = convert()
    OUTPUT_JSON.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JSON} with {len(tasks)} tasks")


if __name__ == "__main__":
    main()
