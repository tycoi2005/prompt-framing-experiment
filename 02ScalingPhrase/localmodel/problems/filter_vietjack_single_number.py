"""Build a strict single-answer VietJack math dataset.

This uses the crawled question CSV rather than the first converted JSON because
the original solution text is needed to infer final scalar answers from worked
solutions.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from convert_vietjack_to_math_json import build_essay_prompt, build_multiple_choice_prompt


INPUT_CSV = Path("vietjack_onvao10_2026/questions.csv")
OUTPUT_JSON = Path("VietJack_OnVao10_2026.math.v1.json")
AUDIT_CSV = Path("VietJack_OnVao10_2026.math.v1.audit.csv")

MULTI_OR_NONSCALAR_PROMPT_RE = re.compile(
    r"(^|\s)(a\)|b\)|c\)|d\)|1\)|2\)|3\)|4\))"
    r"|\([a-d]\)|\([1-4]\)"
    r"|chứng minh|rút gọn|vẽ|lập bảng|biểu đồ|đồ thị"
    r"|bảng|hình|hình ảnh|hình vẽ|bên dưới|sau đây"
    r"|giải phương trình|tìm các|tìm 2 số|hai nghiệm|mỗi loại|mỗi tổ|mỗi người"
    r"|lần lượt|mỗi sản phẩm|bao nhiêu tờ.*mỗi loại|tốc độ của mỗi|các biến cố"
    r"|điều kiện xác định|tính tần số|tần số tương đối|hệ số a.*có thể",
    flags=re.I,
)

SCALAR_PROMPT_RE = re.compile(
    r"bao nhiêu|tính|tìm|xác suất|giá trị|diện tích|chiều cao|số sản phẩm|"
    r"số quyển|số xe|số tiền|quãng đường|thời gian|hệ số",
    flags=re.I,
)

CONCLUSION_RE = re.compile(
    r"(vậy|do đó|suy ra|kết quả|xác suất|diện tích|chiều cao|thời gian|"
    r"quãng đường|số [^\\.\\n]{0,40} là|cần|bằng)",
    flags=re.I,
)

NUMBER_RE = re.compile(
    r"(?<![\w])[-+]?(?:\d+\s*/\s*\d+|\d+(?:[,.]\d+)?)(?![\w])"
)
LATEX_FRAC_RE = re.compile(
    r"\\frac\s*\{+\s*([-+]?\d+(?:[,.]\d+)?)\s*\}+"
    r"\s*\{+\s*([-+]?\d+(?:[,.]\d+)?)\s*\}+"
)


def clean_number(token: str) -> str:
    return re.sub(r"\s+", "", token).replace(",", ".")


def normalize_math_text(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"{clean_number(match.group(1))}/{clean_number(match.group(2))}"

    text = LATEX_FRAC_RE.sub(repl, text or "")
    text = text.replace("\\,", "")
    text = re.sub(r"\\\[|\\\]|\\\(|\\\)", " ", text)
    text = re.sub(r"(?<=\d)[ \u00a0]+(?=\d{3}\b)", "", text)
    return text


def split_sentences(text: str) -> list[str]:
    text = normalize_math_text(text)
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?。])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def choose_conclusion(reason: str) -> str:
    sentences = split_sentences(reason)
    if not sentences:
        return ""
    for sentence in reversed(sentences):
        if CONCLUSION_RE.search(sentence):
            return sentence
    return sentences[-1]


def extract_scalar_answer(prompt: str, reason: str) -> tuple[str | None, str]:
    conclusion = choose_conclusion(reason)
    numbers = [clean_number(match.group(0)) for match in NUMBER_RE.finditer(conclusion)]
    fractions = [n for n in numbers if "/" in n]

    if "xác suất" in prompt.lower() or "xác xuất" in prompt.lower():
        if fractions:
            return fractions[-1], conclusion

    # If the prompt asks for a specific unit, prefer the final value in that unit.
    unit_preferences = [
        ("phút", r"([-+]?\d+(?:[,.]\d+)?)\s*phút"),
        ("giây", r"([-+]?\d+(?:[,.]\d+)?)\s*giây"),
        ("mét vuông", r"([-+]?\d+(?:[,.]\d+)?)\s*(?:mét vuông|m\^?2|m2)"),
        ("m2", r"([-+]?\d+(?:[,.]\d+)?)\s*(?:mét vuông|m\^?2|m2)"),
        ("m", r"([-+]?\d+(?:[,.]\d+)?)\s*m\b"),
        ("km/h", r"([-+]?\d+(?:[,.]\d+)?)\s*km/h"),
        ("quyển", r"([-+]?\d+(?:[,.]\d+)?)\s*quyển"),
        ("xe", r"([-+]?\d+(?:[,.]\d+)?)\s*xe"),
        ("sản phẩm", r"([-+]?\d+(?:[,.]\d+)?)\s*sản phẩm"),
        ("đồng", r"([-+]?\d+(?:[,.]\d+)?)\s*(?:đồng|nghìn đồng)"),
        ("%", r"([-+]?\d+(?:[,.]\d+)?)\s*%"),
    ]
    prompt_lower = prompt.lower()
    for cue, pattern in unit_preferences:
        if cue in prompt_lower:
            matches = re.findall(pattern, conclusion, flags=re.I)
            if matches:
                return clean_number(matches[-1]), conclusion

    if len(numbers) == 1:
        if set(numbers[0]) == {"0"}:
            return None, conclusion
        return numbers[0], conclusion

    # Common conclusion style: "720 giây = 12 phút"; choose the last scalar.
    if len(numbers) == 2 and "=" in conclusion:
        return numbers[-1], conclusion

    return None, conclusion


def is_likely_single_scalar_prompt(prompt: str) -> bool:
    normalized = re.sub(r"\s+", " ", prompt).strip()
    if not SCALAR_PROMPT_RE.search(normalized):
        return False
    if MULTI_OR_NONSCALAR_PROMPT_RE.search(normalized):
        return False
    return True


def convert_rows() -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    tasks: list[dict[str, object]] = []
    audit_rows: list[dict[str, str]] = []
    with INPUT_CSV.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["question_type"] == "test":
                prompt, letter = build_multiple_choice_prompt(row)
                answers = json.loads(row.get("answers_json") or "[]")
                expected_answer = None
                conclusion = ""
                for index, answer in enumerate(answers):
                    text = answer.get("content_text", "")
                    if answer.get("answer") == "Y":
                        nums = [clean_number(m.group(0)) for m in NUMBER_RE.finditer(text)]
                        if len(nums) == 1:
                            expected_answer = nums[0]
                            conclusion = f"Correct option {letter}: {text}"
                        break
            else:
                prompt, reason = build_essay_prompt(row)
                expected_answer, conclusion = extract_scalar_answer(prompt, reason)

            if not is_likely_single_scalar_prompt(prompt) or expected_answer is None:
                continue

            task = {
                "id": f"vietjack_math_v1_{len(tasks) + 1:04d}",
                "category": "math",
                "difficulty": "medium",
                "prompt": prompt,
                "expected_answer": expected_answer,
                "source_task_id": int(row["question_id"]),
                "source_old_id": int(row["exam_id"]),
            }
            tasks.append(task)
            audit_rows.append(
                {
                    "id": task["id"],
                    "expected_answer": str(expected_answer),
                    "question_id": row["question_id"],
                    "exam_id": row["exam_id"],
                    "test_title": row["test_title"],
                    "conclusion": conclusion,
                }
            )
    return tasks, audit_rows


def main() -> None:
    tasks, audit_rows = convert_rows()
    OUTPUT_JSON.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "id",
            "expected_answer",
            "question_id",
            "exam_id",
            "test_title",
            "conclusion",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"Wrote {OUTPUT_JSON} with {len(tasks)} tasks")
    print(f"Wrote {AUDIT_CSV} with {len(audit_rows)} audit rows")


if __name__ == "__main__":
    main()
