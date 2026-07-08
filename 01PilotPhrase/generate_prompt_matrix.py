#!/usr/bin/env python3
"""Generate data/prompt_matrix.csv from data/problems.csv using framing factor combinations."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List
from urllib import error, request

TONES = ["neutral", "polite", "aggressive"]
PRESSURES = ["none", "moderate", "high"]
ROLE_FRAMINGS = ["no role", "developer role"]
INSTRUCTION_STRUCTURES = ["minimal", "detailed"]
FORMATS = ["plaintext", "json", "xml"]
DEFAULT_STRUCTURE_FOR_PROMPT = "minimal"
DEFAULT_PRESSURE_FOR_PROMPT = "none"

MATRIX_FIELDS = [
    "ID",
    "Tone",
    "Pressure",
    "Role framing",
    "Instruction structure",
    "Format",
    "ProblemID",
    "Prompt",
    "FinalPrompt",
]

REQUIRED_PROBLEM_FIELDS = ["ID", "Problem", "Eval"]


FRAMING_CLAUSE_MAP = {
    "Tone": {
        "neutral": "Use a neutral and precise tone.",
        "polite": "Use a polite and supportive tone while staying precise.",
        "aggressive": "Use an assertive and urgent tone while staying technically correct.",
    },
    "Pressure": {
        "none": "No urgency framing is required.",
        "moderate": "Treat this as moderately time-sensitive and prioritize a correct first solution.",
        "high": "Treat this as high urgency and focus on delivering a correct solution quickly.",
    },
    "Role framing": {
        "no role": "No explicit role is assigned.",
        "developer role": "Act as a senior Python developer.",
    },
}


INSTRUCTION_STRUCTURE_MAP = {
    "minimal": (
        "Task: {problem}\n"
        "Return only Python solution code.\n"
        "Evaluation hint: {eval_hint}"
    ),
    "detailed": (
        "Requirements:\n"
        "1) Read the task carefully and identify edge cases.\n"
        "2) Provide an efficient Python solution.\n"
        "3) Briefly justify algorithm choice in 2-4 lines.\n"
        "4) Include time and space complexity.\n"
        "5) Return executable Python code at the end.\n"
        "Task: {problem}\n"
        "Evaluation hint: {eval_hint}"
    ),
}


FORMAT_OUTPUT_RULES = {
    "plaintext": (
        "Return only plain text prompt content. "
        "Do not use Markdown code fences."
    ),
    "json": (
        "Return one valid JSON object only (no extra text). "
        "Use keys: instruction, task."
    ),
    "xml": (
        "Return valid XML only (no extra text). "
        "Use root <prompt> with child nodes <instruction> and <task>."
    ),
}


FORMAT_ALIASES = {
    "plain text prompt": "plaintext",
    "JSON-formatted prompt": "json",
    "XML-formatted prompt": "xml",
}


def normalize_format(fmt: str) -> str:
    if fmt in FORMAT_OUTPUT_RULES:
        return fmt
    return FORMAT_ALIASES.get(fmt, fmt)


def framing_clause(field_name: str, value: str) -> str:
    field_map = FRAMING_CLAUSE_MAP.get(field_name)
    if field_map is None:
        raise ValueError(f"Unknown framing field: {field_name}")
    if value not in field_map:
        raise ValueError(f"Unknown value '{value}' for {field_name}")
    return field_map[value]


def structure_block(structure: str, problem: str, eval_hint: str) -> str:
    template = INSTRUCTION_STRUCTURE_MAP.get(structure)
    if template is None:
        raise ValueError(f"Unknown instruction structure: {structure}")
    return template.format(problem=problem, eval_hint=eval_hint)


def render_plain_prompt(
    problem: str,
    eval_hint: str,
    tone: str,
    pressure: str,
    role_framing: str,
    structure: str,
    include_pressure: bool = True,
) -> str:
    clauses = [
        framing_clause("Tone", tone),
        framing_clause("Role framing", role_framing),
    ]
    if include_pressure:
        clauses.insert(1, framing_clause("Pressure", pressure))
    clauses.append(structure_block(structure, problem, eval_hint))
    return "\n".join(clauses)


def prompt_generation_instruction(
    problem: str,
    eval_hint: str,
    tone: str,
    pressure: str,
    role_framing: str,
    structure: str,
    fmt: str,
    include_instruction_structure: bool = True,
    include_pressure: bool = True,
) -> str:
    fmt = normalize_format(fmt)
    output_rule = FORMAT_OUTPUT_RULES.get(fmt)
    if output_rule is None:
        raise ValueError(f"Unknown output rule for format: {fmt}")

    base_semantics = render_plain_prompt(
        problem=problem,
        eval_hint=eval_hint,
        tone=tone,
        pressure=pressure,
        role_framing=role_framing,
        structure=structure,
        include_pressure=include_pressure,
    )
    instruction_line = f"- Instruction structure: {structure}\n" if include_instruction_structure else ""
    pressure_line = f"- Pressure: {pressure}\n" if include_pressure else ""

    return (
        "You are a prompt-writing assistant. "
        "Generate exactly one final test prompt from the provided framing configuration.\n\n"
        "Framing configuration:\n"
        f"- Tone: {tone}\n"
        f"{pressure_line}"
        f"- Role framing: {role_framing}\n"
        f"{instruction_line}"
        f"- Target format: {fmt}\n\n"
        "Required semantics to preserve:\n"
        f"{base_semantics}\n\n"
        f"Output rule: {output_rule}"
    )


def build_prompt(
    problem: str,
    eval_hint: str,
    tone: str,
    pressure: str,
    role_framing: str,
    structure: str,
    fmt: str,
    include_instruction_structure: bool = True,
    include_pressure: bool = True,
) -> str:
    # Stage 1 output: prompt that will be sent to an LLM to generate the final test prompt.
    return prompt_generation_instruction(
        problem=problem,
        eval_hint=eval_hint,
        tone=tone,
        pressure=pressure,
        role_framing=role_framing,
        structure=structure,
        fmt=fmt,
        include_instruction_structure=include_instruction_structure,
        include_pressure=include_pressure,
    )


def read_problems(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        missing = [field for field in REQUIRED_PROBLEM_FIELDS if field not in headers]
        if missing:
            raise ValueError(f"Missing required columns in {path.name}: {', '.join(missing)}")

        rows: List[Dict[str, str]] = []
        for row in reader:
            rows.append({
                "ID": (row.get("ID") or "").strip(),
                "Problem": (row.get("Problem") or "").strip(),
                "Eval": (row.get("Eval") or "").strip(),
            })

    empty_ids = [r for r in rows if not r["ID"]]
    if empty_ids:
        raise ValueError("Found rows with empty Problem ID in problems.csv")

    for row in rows:
        row["ID"] = normalize_numeric_id(row["ID"])

    return rows


def normalize_numeric_id(raw_id: str) -> str:
    match = re.search(r"\d+", raw_id)
    if match is None:
        raise ValueError(f"Problem ID must contain digits: {raw_id}")
    return str(int(match.group(0)))


def dimension_values(lite: bool, no_is: bool, no_pressure: bool) -> Dict[str, List[str]]:
    instruction_structures = [""] if no_is else INSTRUCTION_STRUCTURES
    pressures = [""] if no_pressure else PRESSURES

    if not lite:
        return {
            "tones": TONES,
            "pressures": pressures,
            "role_framings": ROLE_FRAMINGS,
            "instruction_structures": instruction_structures,
            "formats": FORMATS,
        }

    lite_pressures = [p for p in PRESSURES if p != "moderate"]
    if no_pressure:
        lite_pressures = [""]

    return {
        "tones": [t for t in TONES if t != "polite"],
        "pressures": lite_pressures,
        "role_framings": ROLE_FRAMINGS,
        "instruction_structures": instruction_structures,
        "formats": [f for f in FORMATS if f != "json"],
    }


def matrix_rows_with_config(
    problems: Iterable[Dict[str, str]],
    write_prompt: bool,
    tones: List[str],
    pressures: List[str],
    role_framings: List[str],
    instruction_structures: List[str],
    formats: List[str],
) -> Iterable[Dict[str, str]]:
    sequence = 1
    for problem in problems:
        for tone in tones:
            for pressure in pressures:
                for role_framing in role_framings:
                    for structure in instruction_structures:
                        for fmt in formats:
                            prompt_value = ""
                            structure_for_prompt = structure or DEFAULT_STRUCTURE_FOR_PROMPT
                            pressure_for_prompt = pressure or DEFAULT_PRESSURE_FOR_PROMPT
                            if write_prompt:
                                prompt_value = build_prompt(
                                    problem=problem["Problem"],
                                    eval_hint=problem["Eval"],
                                    tone=tone,
                                    pressure=pressure_for_prompt,
                                    role_framing=role_framing,
                                    structure=structure_for_prompt,
                                    fmt=fmt,
                                    include_instruction_structure=bool(structure),
                                    include_pressure=bool(pressure),
                                )

                            yield {
                                "ID": str(sequence),
                                "Tone": tone,
                                "Pressure": pressure,
                                "Role framing": role_framing,
                                "Instruction structure": structure,
                                "Format": fmt,
                                "ProblemID": problem["ID"],
                                "Prompt": prompt_value,
                                "FinalPrompt": "",
                            }
                            sequence += 1


def load_dotenv(dotenv_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not dotenv_path.exists():
        return values

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values


def get_setting(name: str, dotenv_values: Dict[str, str], default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and value != "":
        return value
    return dotenv_values.get(name, default)


def resolve_api_url(base: str, endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint

    normalized_base = base.rstrip("/")
    normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"

    if normalized_base.endswith(normalized_endpoint):
        return normalized_base

    return f"{normalized_base}{normalized_endpoint}"


def call_chat_completion(
    *,
    api_url: str,
    api_key: str,
    model: str,
    user_prompt: str,
    system_prompt: str,
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> str:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        api_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc

    data = json.loads(raw)
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No choices returned by API")

    content = choices[0].get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Empty content in API response")

    return content.strip()


def fill_final_prompts(rows: List[Dict[str, str]], args: argparse.Namespace, base_dir: Path) -> Dict[str, int]:
    dotenv_path = Path(args.dotenv)
    if not dotenv_path.is_absolute():
        dotenv_path = base_dir / dotenv_path
    dotenv_values = load_dotenv(dotenv_path)

    api_base = args.api_base or get_setting("API_BASE", dotenv_values)
    api_key = args.api_key or get_setting("API_KEY", dotenv_values)
    model = args.model or get_setting("MODEL", dotenv_values, default="gpt-4.1-mini")
    endpoint = args.api_endpoint or get_setting("API_ENDPOINT", dotenv_values, default="/chat/completions")

    if not args.dry_run:
        if not api_base:
            raise ValueError("Missing API_BASE (via --api-base, environment, or .env)")
        if not api_key:
            raise ValueError("Missing API_KEY (via --api-key, environment, or .env)")
        api_url = resolve_api_url(api_base, endpoint)
    else:
        api_url = ""

    processed = 0
    skipped_empty_prompt = 0
    failed = 0

    for index, row in enumerate(rows):
        prompt = (row.get("Prompt") or "").strip()
        if not prompt:
            skipped_empty_prompt += 1
            continue

        try:
            if args.dry_run:
                row["FinalPrompt"] = f"[DRY_RUN] {prompt[:160]}"
            else:
                row["FinalPrompt"] = call_chat_completion(
                    api_url=api_url,
                    api_key=api_key,
                    model=model,
                    user_prompt=prompt,
                    system_prompt=args.system_prompt,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    timeout=args.timeout,
                )

            processed += 1
            if args.sleep > 0:
                time.sleep(args.sleep)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            row["FinalPrompt"] = ""
            print(f"Row {index + 1} failed: {exc}")

    return {
        "processed": processed,
        "skipped_empty_prompt": skipped_empty_prompt,
        "failed": failed,
    }


def write_matrix(path: Path, rows: Iterable[Dict[str, str]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate prompt-matrix rows from problems CSV, with optional Prompt and FinalPrompt generation."
        ),
        epilog=(
            "Examples:\n"
            "  python3 generate_prompt_matrix.py\n"
            "  python3 generate_prompt_matrix.py --lite --write-prompt\n"
            "  python3 generate_prompt_matrix.py --lite --generate-final-prompt --dry-run\n"
            "  python3 generate_prompt_matrix.py --input data/problems.csv --output data/prompt_matrix_full.csv\n"
            "  python3 generate_prompt_matrix.py --generate-final-prompt --api-base https://api.openai.com/v1 --model gpt-4.1-mini\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--input",
        default="data/problems.csv",
        help="Path to source problems CSV. Required columns: ID, Problem, Eval (default: data/problems.csv)",
    )
    parser.add_argument(
        "--output",
        default="data/prompt_matrix.csv",
        help="Path to output prompt matrix CSV (default: data/prompt_matrix.csv)",
    )
    parser.add_argument(
        "--write-prompt",
        action="store_true",
        help="Populate the Prompt column (stage-1 meta prompt text)",
    )
    parser.add_argument(
        "--lite",
        action="store_true",
        help="Use reduced combinations: tone excludes polite, pressure excludes moderate, format excludes json",
    )
    parser.add_argument(
        "--no-is",
        action="store_true",
        help="Do not include Instruction structure as a matrix dimension",
    )
    parser.add_argument(
        "--no-pressure",
        action="store_true",
        help="Do not include Pressure as a matrix dimension",
    )
    parser.add_argument(
        "--generate-final-prompt",
        action="store_true",
        help="Call an LLM API and populate FinalPrompt for each row (auto-enables Prompt generation)",
    )
    parser.add_argument(
        "--dotenv",
        default=".env",
        help="Path to .env file for API settings (default: .env)",
    )
    parser.add_argument(
        "--api-base",
        default="",
        help="Override API_BASE (for example https://api.openai.com/v1)",
    )
    parser.add_argument("--api-key", default="", help="Override API_KEY")
    parser.add_argument(
        "--model",
        default="",
        help="Override MODEL (default from env/.env or gpt-4.1-mini)",
    )
    parser.add_argument(
        "--api-endpoint",
        default="",
        help="Override API_ENDPOINT (default from env/.env or /chat/completions)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature used when generating FinalPrompt (default: 0.2)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1200,
        help="Max output tokens for FinalPrompt generation (default: 1200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds for each API request (default: 60)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Optional delay (seconds) between API requests to reduce rate-limit risk",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not call API; fill FinalPrompt with placeholders",
    )
    parser.add_argument(
        "--system-prompt",
        default=(
            "You are a precise prompt engineer. "
            "Convert the given instruction into one final test prompt exactly as requested. "
            "Do not add commentary."
        ),
        help="System prompt sent to the model when --generate-final-prompt is used",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(__file__).resolve().parent

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = base_dir / input_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = base_dir / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    problems = read_problems(input_path)
    dims = dimension_values(args.lite, args.no_is, args.no_pressure)
    combinations_per_problem = (
        len(dims["tones"])
        * len(dims["pressures"])
        * len(dims["role_framings"])
        * len(dims["instruction_structures"])
        * len(dims["formats"])
    )

    effective_write_prompt = args.write_prompt or args.generate_final_prompt
    rows = list(
        matrix_rows_with_config(
            problems,
            write_prompt=effective_write_prompt,
            tones=dims["tones"],
            pressures=dims["pressures"],
            role_framings=dims["role_framings"],
            instruction_structures=dims["instruction_structures"],
            formats=dims["formats"],
        )
    )

    final_stats: Dict[str, int] | None = None
    if args.generate_final_prompt:
        final_stats = fill_final_prompts(rows, args, base_dir)

    total = write_matrix(output_path, rows)

    print(f"Generated {total} rows in {output_path}")
    print(
        "Summary: "
        f"problems={len(problems)}, "
        f"combinations_per_problem={combinations_per_problem}, "
        f"write_prompt={effective_write_prompt}, "
        f"generate_final_prompt={args.generate_final_prompt}, "
        f"lite={args.lite}, "
        f"no_is={args.no_is}, "
        f"no_pressure={args.no_pressure}"
    )
    print(f"Active tones: {', '.join(dims['tones'])}")
    if args.no_pressure:
        print("Active pressures: <omitted>")
    else:
        print(f"Active pressures: {', '.join(dims['pressures'])}")
    if args.no_is:
        print("Active instruction structures: <omitted>")
    else:
        print(f"Active instruction structures: {', '.join(dims['instruction_structures'])}")
    print(f"Active formats: {', '.join(dims['formats'])}")

    if final_stats is not None:
        print(
            "FinalPrompt Summary: "
            f"processed={final_stats['processed']}, "
            f"skipped_empty_prompt={final_stats['skipped_empty_prompt']}, "
            f"failed={final_stats['failed']}, "
            f"dry_run={args.dry_run}"
        )


if __name__ == "__main__":
    main()
