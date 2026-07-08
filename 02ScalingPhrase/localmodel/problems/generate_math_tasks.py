"""Generate math-reasoning tasks from the original Python-style problem JSON."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_PATH = Path("VNSchoolMathProblems_lite.v0.7.json")
DEFAULT_OUTPUT_PATH = Path("VNSchoolMathProblems_lite.v0.7.math.json")


PROMPT_OVERRIDES = {
    4: (
        "An elliptical garden has major axis length {major_axis} m and minor axis "
        "length {minor_axis} m. A semicircular grass area of radius "
        "{semi_circle_radius} m is removed from the ellipse. Calculate the "
        "remaining paved area in square meters, rounded to two decimal places."
    ),
    9: (
        "A square wooden board has side length {side_length} cm. The shaded "
        "crab-shaped region is modeled by the area formula "
        "side_length^2 - pi * (side_length / 3)^2. Calculate the shaded area, "
        "rounded to the nearest integer."
    ),
    32: (
        "Find the minimum distance, in meters, from the point M({mx}, {my}) to "
        "the curve g(x) = (x + 1) / (x - 2) for x > 2. One coordinate unit is "
        "10 meters. Round the result to two decimal places."
    ),
    49: (
        "A board game surface is made from a central rectangle of length "
        "{length} cm and width {width} cm together with the fixed surrounding "
        "decorative regions from the original design. The coating cost is "
        "{cost_per_m2} VND per square meter. Calculate the total coating cost "
        "in thousands of VND, rounded to the nearest integer."
    ),
}


TASK_LABELS = {
    1: {
        "n": "total number of tickets n",
        "target_sum": "target sum for each group",
        "reward_per_group": "reward per valid group in VND",
    },
    2: {"a": "cardboard side length a in cm"},
    3: {
        "type1_expired": "expired cans in each Type I case",
        "type2_expired": "expired cans in each Type II case",
        "total_cans": "cans per case",
        "sample_size": "number of cans sampled",
        "expired_found": "expired cans found in the sample",
        "ratio_type1_to_type2": "ratio of Type I cases to Type II cases",
    },
    4: {
        "major_axis": "ellipse major axis length in meters",
        "minor_axis": "ellipse minor axis length in meters",
        "semi_circle_radius": "semicircle radius in meters",
    },
    5: {"dist_matrix": "distance matrix between the five cities"},
    6: {
        "total_chairs": "total number of chairs",
        "num_students": "number of students",
    },
    7: {
        "current_wells": "current number of wells",
        "current_yield": "current daily yield per well",
        "yield_decrease": "yield decrease per well for each additional well",
    },
    8: {
        "lemonade_limit": "available cups of lemonade",
        "fries_limit": "available portions of fries",
        "price_a": "price of Combo A in thousand VND",
        "lemonade_a": "cups of lemonade in Combo A",
        "fries_a": "portions of fries in Combo A",
        "price_b": "price of Combo B in thousand VND",
        "lemonade_b": "cups of lemonade in Combo B",
        "fries_b": "portions of fries in Combo B",
    },
    10: {
        "current_freq": "current string frequency in Hz",
        "target_note_freq": "target E4 frequency in Hz",
        "angle_per_semitone": "peg rotation angle per semitone in degrees",
    },
    14: {
        "raw_material_limit": "available raw material in kg",
        "hour_limit": "available working hours",
        "type1_mat": "raw material needed per kg of Type I",
        "type1_hour": "working hours needed per kg of Type I",
        "type1_profit": "profit per kg of Type I in thousand VND",
        "type2_mat": "raw material needed per kg of Type II",
        "type2_hour": "working hours needed per kg of Type II",
        "type2_profit": "profit per kg of Type II in thousand VND",
    },
    20: {"distances": "distance table between locations"},
    24: {
        "p_male": "survival probability of one male gosling",
        "p_female": "survival probability of one female gosling",
        "n_male": "number of male goslings",
        "n_female": "number of female goslings",
    },
    34: {
        "max_area": "maximum planting area in hectares",
        "pomelo_labor": "labor days per hectare of green pomelo",
        "pomelo_cap": "capital per hectare of green pomelo in million VND",
        "orange_labor": "labor days per hectare of king orange",
        "orange_cap": "capital per hectare of king orange in million VND",
        "max_labor": "available labor days",
        "max_cap": "available capital in million VND",
        "pomelo_profit": "profit per hectare of green pomelo in million VND",
        "orange_profit": "profit per hectare of king orange in million VND",
    },
    39: {
        "initial_price": "initial selling price in thousand VND per kg",
        "initial_orders": "initial weekly orders",
        "initial_qty": "initial quantity per order in kg",
        "price_step": "price increase step in thousand VND per kg",
        "order_dec": "weekly order decrease per price step",
        "qty_dec": "quantity decrease per order per price step in kg",
        "cost_price": "cost price in thousand VND per kg",
        "max_price": "maximum selling price in thousand VND per kg",
    },
    50: {
        "debt": "total debt",
        "percentage": "target fraction of the debt to pay",
        "months": "number of months",
        "ratio": "monthly payment ratio relative to the previous month",
    },
}


def clean_problem_text(text: str) -> str:
    replacements = [
        (r"^Write a function to calculate ", "Calculate "),
        (r"^Write a function to find ", "Find "),
        (r"^Write a function to determine ", "Determine "),
        (r"^Write a function to count ", "Count "),
        (r"^Write a function to solve ", "Solve "),
        (r"^Write a function to ", ""),
        (r"The function accepts ", "Use "),
        (r"the function accepts ", "use "),
        (
            r"Generalize the function to accept the starting number of pages and the daily increment\.",
            "The starting number of pages and daily increment may vary.",
        ),
        (
            r"The function should take distance AB, distance to the road, desert speed, and road speed as parameters\.",
            "The relevant quantities are the distance AB, the distance to the road, the desert speed, and the road speed.",
        ),
        (
            r"The function should take the coefficients of the cost and price functions as parameters\.",
            "The relevant quantities are the coefficients of the cost expression and the price expression.",
        ),
        (r"For the purpose of this function, calculate", "For this instance, calculate"),
    ]

    cleaned = text.strip()
    for pattern, repl in replacements:
        cleaned = re.sub(pattern, repl, cleaned)
    return cleaned


def parse_first_assert(assertion: str) -> tuple[ast.AST, Any]:
    tree = ast.parse(assertion)
    stmt = tree.body[0]
    if not isinstance(stmt, ast.Assert):
        raise ValueError(f"Unsupported test statement: {assertion}")
    comp = stmt.test
    if not isinstance(comp, ast.Compare) or len(comp.comparators) != 1:
        raise ValueError(f"Unsupported assertion shape: {assertion}")
    return comp.left, ast.literal_eval(comp.comparators[0])


def unwrap_round(expr: ast.AST) -> tuple[ast.AST, str | None]:
    if (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == "round"
        and expr.args
    ):
        digits = ast.unparse(expr.args[1]) if len(expr.args) > 1 else None
        return expr.args[0], digits
    return expr, None


def render_value_node(node: ast.AST) -> Any:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "list"
        and node.args
    ):
        inner = node.args[0]
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "range"
        ):
            args = [ast.literal_eval(arg) for arg in inner.args]
            return list(range(*args))
    return ast.literal_eval(node)


def render_value(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(render_value(v) for v in value) + "]"
    if isinstance(value, tuple):
        return "(" + ", ".join(render_value(v) for v in value) + ")"
    if isinstance(value, dict):
        items = []
        for key, val in value.items():
            items.append(f"{render_value(key)}: {render_value(val)}")
        return "{" + ", ".join(items) + "}"
    return str(value)


def extract_function_args(code: str) -> tuple[list[str], dict[str, Any]]:
    tree = ast.parse(code)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if not functions:
        return [], {}
    func = functions[-1]
    args = [arg.arg for arg in func.args.args]
    defaults: dict[str, Any] = {}
    if func.args.defaults:
        default_args = args[-len(func.args.defaults) :]
        for name, node in zip(default_args, func.args.defaults):
            try:
                defaults[name] = render_value_node(node)
            except Exception:
                pass
    return args, defaults


def call_values(expr: ast.AST, arg_names: list[str], defaults: dict[str, Any]) -> dict[str, Any]:
    expr, _ = unwrap_round(expr)
    if not isinstance(expr, ast.Call):
        return defaults.copy()

    values = defaults.copy()
    for name, node in zip(arg_names, expr.args):
        values[name] = render_value_node(node)
    for keyword in expr.keywords:
        if keyword.arg:
            values[keyword.arg] = render_value_node(keyword.value)
    return {name: values[name] for name in arg_names if name in values}


def label_for(task_id: int, arg_name: str) -> str:
    labels = TASK_LABELS.get(task_id, {})
    if arg_name in labels:
        return labels[arg_name]
    return arg_name.replace("_", " ")


def format_given_lines(task_id: int, values: dict[str, Any]) -> str:
    if not values:
        return ""
    lines = ["Given:"]
    for name, value in values.items():
        lines.append(f"- {label_for(task_id, name)} = {render_value(value)}")
    return "\n".join(lines)


def prompt_text(task: dict[str, Any], values: dict[str, Any], round_digits: str | None) -> str:
    task_id = int(task["task_id"])
    if task_id in PROMPT_OVERRIDES:
        text = PROMPT_OVERRIDES[task_id].format(**values)
        given = ""
    else:
        text = clean_problem_text(task["text"])
        given = format_given_lines(task_id, values)

    parts = [text]
    if given:
        parts.append(given)
    if round_digits is not None:
        parts.append(f"Round the computed value to {round_digits} decimal places.")

    final_question = "With these values, what is the result?"
    if task_id == 24:
        final_question += " Write the results separated by commas."
    parts.append(final_question)
    return "\n\n".join(parts)


def generate_math_tasks(
    source_path: Path = DEFAULT_SOURCE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> list[dict[str, Any]]:
    tasks = json.loads(source_path.read_text(encoding="utf-8"))
    math_tasks = []

    for task in tasks:
        expr, expected_answer = parse_first_assert(task["test_list"][0])
        expr, round_digits = unwrap_round(expr)
        arg_names, defaults = extract_function_args(task["code"])
        values = call_values(expr, arg_names, defaults)

        math_tasks.append(
            {
                "id": f"math_{int(task['task_id']):03d}",
                "category": "math",
                "difficulty": task.get("difficulty", "unknown"),
                "prompt": prompt_text(task, values, round_digits),
                "expected_answer": expected_answer,
                "source_task_id": task["task_id"],
                "source_old_id": task.get("old_id"),
            }
        )

    output_path.write_text(
        json.dumps(math_tasks, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return math_tasks


def main() -> None:
    tasks = generate_math_tasks()
    print(f"Generated {len(tasks)} math tasks in {DEFAULT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
