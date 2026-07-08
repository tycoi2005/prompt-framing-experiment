"""Generate problem.math.csv from math reasoning tasks and prompt templates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_TASKS_PATH = Path("VNSchoolMathProblems_lite.v0.7.math.json")
DEFAULT_TEMPLATES_PATH = Path("prompt_matrix_prompt_template.08.math.csv")
DEFAULT_OUTPUT_PATH = Path("problem.math.csv")


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def normalize_template_text(text: str) -> str:
    """Convert coding-oriented template wording into math-reasoning wording."""
    replacements = {
        "Complete the following Python requirement precisely as specified.": (
            "Solve the following math problem precisely as specified."
        ),
        "Follow standard production practices, including full type hints and error handling.": (
            "Use careful mathematical reasoning."
        ),
        "Return only the requested output.": "Return only the requested result.",
        "help me solve this Python problem": "help me solve this math problem",
        "provide a high-quality solution": "provide an accurate result",
        "ensure the code is modular, includes full type hints, and handles errors correctly": (
            "ensure the calculation is careful and accurate"
        ),
        "production-quality code, full type hints, and proper error handling": (
            "a careful, accurate mathematical result"
        ),
        "code, full type hints, and proper error handling": (
            "reasoning, careful arithmetic, and a precise final result"
        ),
        "Python problem": "math problem",
        "Python requirement": "math problem",
    }

    normalized = text
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def render_expected_answer(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_prompt(template_text: str, fmt: str, math_prompt: str) -> str:
    template_text = normalize_template_text(template_text)
    fmt = fmt.lower()

    placeholders = ("{MATH_PROBLEM}", "{PYTHON_PROBLEM}")

    if "json" in fmt:
        try:
            data = json.loads(template_text)
        except json.JSONDecodeError:
            for placeholder in placeholders:
                template_text = template_text.replace(placeholder, math_prompt)
            return template_text

        for key, value in data.items():
            if isinstance(value, str):
                for placeholder in placeholders:
                    value = value.replace(placeholder, math_prompt)
                data[key] = value
        return json.dumps(data, indent=2, ensure_ascii=False)

    if "xml" in fmt:
        for placeholder in placeholders:
            template_text = template_text.replace(placeholder, escape_xml(math_prompt))
        return template_text

    for placeholder in placeholders:
        template_text = template_text.replace(placeholder, math_prompt)
    return template_text


def load_tasks(path: Path, limit: int | None) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        tasks = json.load(f)

    if limit is not None and limit > 0:
        return tasks[:limit]
    return tasks


def load_templates(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def generate_math_prompts(
    tasks_path: Path = DEFAULT_TASKS_PATH,
    templates_path: Path = DEFAULT_TEMPLATES_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    limit: int | None = None,
) -> int:
    tasks = load_tasks(tasks_path, limit)
    templates = load_templates(templates_path)

    with output_path.open("w", encoding="utf-8", newline="") as csvfile:
        fieldnames = [
            "task_id",
            "category_id",
            "prompt",
            "expected_answer",
            "difficulty",
            "source_task_id",
            "source_old_id",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        row_count = 0
        for problem_index, task in enumerate(tasks, start=1):
            csv_task_id = f"math_{problem_index:03d}"
            for template in templates:
                writer.writerow(
                    {
                        "task_id": csv_task_id,
                        "category_id": template["ID"],
                        "prompt": build_prompt(
                            template["Prompt"],
                            template.get("Format", ""),
                            task["prompt"],
                        ),
                        "expected_answer": render_expected_answer(
                            task["expected_answer"]
                        ),
                        "difficulty": task.get("difficulty", ""),
                        "source_task_id": problem_index,
                        "source_old_id": task.get("id", task.get("source_old_id", "")),
                    }
                )
                row_count += 1

    return row_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate problem.math.csv from math tasks and prompt templates."
    )
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS_PATH)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--number-problem",
        type=int,
        default=None,
        help="Number of math problems to process. Defaults to all.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_count = generate_math_prompts(
        tasks_path=args.tasks,
        templates_path=args.templates,
        output_path=args.output,
        limit=args.number_problem,
    )
    print(f"Generated {row_count} rows in {args.output}")


if __name__ == "__main__":
    main()
