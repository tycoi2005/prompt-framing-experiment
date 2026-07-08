"""Generate problems.csv from Python coding tasks and prompt templates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_TASKS_PATH = Path("VNSchoolMathProblems_lite.v0.7.json")
DEFAULT_TEMPLATES_PATH = Path("prompt_matrix_prompt_template.09.csv")
DEFAULT_OUTPUT_PATH = Path("problems.csv")


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def render_python_problem(task: dict[str, Any]) -> str:
    prompt = str(task["text"]).strip()
    test_cases = task.get("test_list") or []
    if test_cases:
        prompt += "\n\nTest cases:\n" + "\n".join(str(case) for case in test_cases)
    return prompt


def build_prompt(template_text: str, fmt: str, python_problem: str) -> str:
    fmt = fmt.lower()

    if "json" in fmt:
        try:
            data = json.loads(template_text)
        except json.JSONDecodeError:
            return template_text.replace("{PYTHON_PROBLEM}", python_problem)

        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.replace("{PYTHON_PROBLEM}", python_problem)
        return json.dumps(data, indent=2, ensure_ascii=False)

    if "xml" in fmt:
        return template_text.replace("{PYTHON_PROBLEM}", escape_xml(python_problem))

    return template_text.replace("{PYTHON_PROBLEM}", python_problem)


def load_tasks(path: Path, limit: int | None) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        tasks = json.load(f)
    if limit is not None and limit > 0:
        return tasks[:limit]
    return tasks


def load_templates(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def generate_python_prompts(
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
            "test_cases",
            "challenge_test_list",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        row_count = 0
        for task in tasks:
            python_problem = render_python_problem(task)
            for template in templates:
                writer.writerow(
                    {
                        "task_id": task["task_id"],
                        "category_id": template["ID"],
                        "prompt": build_prompt(
                            template["Prompt"],
                            template.get("Format", ""),
                            python_problem,
                        ),
                        "test_cases": json.dumps(
                            task.get("test_list", []), ensure_ascii=False
                        ),
                        "challenge_test_list": json.dumps(
                            task.get("challenge_test_list", []), ensure_ascii=False
                        ),
                    }
                )
                row_count += 1

    return row_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate problems.csv from Python tasks and prompt templates."
    )
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS_PATH)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--number-problem",
        type=int,
        default=None,
        help="Number of Python problems to process. Defaults to all.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_count = generate_python_prompts(
        tasks_path=args.tasks,
        templates_path=args.templates,
        output_path=args.output,
        limit=args.number_problem,
    )
    print(f"Generated {row_count} rows in {args.output}")


if __name__ == "__main__":
    main()
