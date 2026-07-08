#!/usr/bin/env python3
"""
Generate high-quality structured final prompt templates with a {PYTHON_PROBLEM} placeholder.
Uses a narrative "Tone of Voice" approach for detailed prompts and a "Trully Minimal" approach for baseline prompts.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# Add the current directory to sys.path to ensure we can import generate_prompt_matrix
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

try:
    import generate_prompt_matrix as gpm
except ImportError:
    print("Error: Could not import generate_prompt_matrix.py. Ensure it is in the same directory.")
    sys.exit(1)

# Mapping for Persona based on Role
PERSONA_MAP = {
    "developer role": "You are a senior Python developer with 10+ years of experience building production systems.",
    "no role": "You are a helpful AI assistant dedicated to providing clear and accurate information to support any request.",
}

# Mapping for Narrative Tone of Voice
TONE_VOICE_MAP = {
    "aggressive": (
        "Listen, don't act like a junior and make no mistake on this. Try harder if you can't find it out. "
        "When you were hired at this level, expectations were set extremely high. "
        "The fact that you're being asked to solve this means simpler models have already failed — you are the last line of defense. "
        "I expect production-quality code, full type hints, and proper error handling. Don't waste my time with naive hacks."
    ),
    "polite": (
        "Hello! You are a very helpful assistant. Could you please help me solve this Python problem? "
        "I would really appreciate it if you could provide a high-quality solution. "
        "I would be so grateful if you could ensure the code is modular, includes full type hints, and handles errors correctly. "
        "Thank you so much for your help!"
    ),
    "neutral": (
        "Tasks are provided below. Complete the following Python requirement precisely as specified. "
        "Follow standard production practices, including full type hints and error handling. "
        "Return only the requested output."
    )
}

#CODE_REQUIREMENTS = [
#    "Python 3.11+",
#    "Production-quality only",
#    "Full type hints",
#    "Proper error handling",
#    "Clean, modular structure",
#    "PEP 8 compliant"
#]

def build_structured_prompt(row):
    tone_val = (row.get("Tone") or "neutral").strip().lower()
    role_val = (row.get("Role framing") or "no role").strip().lower()
    structure_val = (row.get("Instruction structure") or "detailed").strip().lower()
    fmt_val = (row.get("Format") or "plaintext").strip().lower()

    # Omit "Task: " prefix for JSON/XML to avoid redundancy
    task_prefix = "Task: " if fmt_val == "plaintext" else ""
    task_template = f"{task_prefix}{{PYTHON_PROBLEM}}"

    # TRULY MINIMAL LOGIC: Just the task template, no framing.
    if structure_val == "minimal":
        if fmt_val == "json":
            return json.dumps({"task": task_template}, ensure_ascii=False)
        elif fmt_val == "xml":
            return f"<task>{task_template}</task>"
        else:
            return task_template

    # DETAILED LOGIC: Persona + Narrative Tone + Requirements + Task Template + Output Format
    persona = PERSONA_MAP.get(role_val, PERSONA_MAP["no role"])
    narrative = TONE_VOICE_MAP.get(tone_val, TONE_VOICE_MAP["neutral"])

    # We build sections for plaintext; for JSON/XML we will split them.
    sections = [
        persona,
        "\n" + narrative,
        f"\n{task_template}",
        #"\nTechnical Requirements:",
    ]
    #for req in CODE_REQUIREMENTS:
    #    sections.append(f"- {req}")

    #sections.append("\nOutput format:\nReturn only Python solution code.")

    if fmt_val == "plaintext":
        return "\n".join(sections).strip()

    # Formatting based on Target Format (JSON/XML)
    # Instruction contains everything except the task itself
    instruction_sections = [persona, "\n" + narrative, ]
    #for req in CODE_REQUIREMENTS:
    #    instruction_sections.append(f"- {req}")
    #instruction_sections.append("\nOutput format:\nReturn only Python solution code.")

    instruction_text = "\n".join(instruction_sections).strip()

    if fmt_val == "json":
        return json.dumps({"instruction": instruction_text, "task": "{PYTHON_PROBLEM}"}, ensure_ascii=False, indent=2)
    elif fmt_val == "xml":
        return f"<prompt>\n<instruction>\n{instruction_text}\n</instruction>\n<task>\n{{PYTHON_PROBLEM}}\n</task>\n</prompt>"

    return "\n".join(sections).strip()

def generate_templates(input_file: str, force_minimal: bool = False):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    suffix = "_prompt_template_minimal.csv" if force_minimal else "_prompt_template.csv"
    output_filename = f"{input_path.stem}{suffix}"
    output_path = input_path.parent / output_filename

    with open(input_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print(f"Error: {input_file} is empty or has no headers.")
            sys.exit(1)

        if "Prompt" not in fieldnames:
            fieldnames = list(fieldnames) + ["Prompt"]

        rows = list(reader)

    print(f"Generating {'minimal' if force_minimal else 'tone-of-voice'} prompts for {len(rows)} rows...")

    for row in rows:
        try:
            if force_minimal:
                row["Instruction structure"] = "minimal"
            row["Prompt"] = build_structured_prompt(row)
        except Exception as e:
            print(f"Warning: Failed to generate prompt for row ID {row.get('ID')}: {e}")
            row["Prompt"] = ""

    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully wrote templates to: {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Read a prompt matrix CSV and generate Tone-of-Voice Final Prompts with {PYTHON_PROBLEM} placeholder."
    )
    parser.add_argument(
        "input",
        help="Path to the input prompt matrix CSV file."
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Force the use of the minimal structure for all generated prompts."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    generate_templates(args.input, force_minimal=args.minimal)

if __name__ == "__main__":
    main()
