import json
import csv
import os
import argparse

def escape_xml(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")

def generate_prompts(num_problems=None, generate_files=False):
    # Create problems directory if files are requested
    output_dir = 'problems'
    if generate_files and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load problems
    with open('VNSchoolMathProblems_lite.v0.7.json', 'r', encoding='utf-8') as f:
        problems = json.load(f)

    # If num_problems is specified, slice the problems list
    if num_problems is not None and num_problems > 0:
        problems = problems[:num_problems]

    # Load templates
    templates = []
    with open('prompt_matrix_prompt_template.08.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            templates.append(row)

    # Prepare problems.csv
    csv_file_path = 'problems.csv'
    with open(csv_file_path, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['task_id', 'category_id', 'prompt', 'test_cases', 'challenge_test_list']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        sequence_number = 1
        for problem in problems:
            task_id = problem['task_id']
            problem_text = problem['text']
            test_list = problem.get('test_list', [])
            test_cases_json = json.dumps(test_list, ensure_ascii=False)
            challenge_test_list = problem.get('challenge_test_list', [])
            challenge_test_json = json.dumps(challenge_test_list, ensure_ascii=False)


            # Default combined text for plaintext formats
            test_str = "\n".join(test_list)
            combined_text = f"{problem_text}\n\nTest cases:\n{test_str}"

            for template in templates:
                category_id = template['ID']
                template_text = template['Prompt']
                fmt = template['Format'].lower()

                if 'json' in fmt:
                    try:
                        # Parse template as JSON to add a new key properly
                        data = json.loads(template_text)
                        # Replace placeholder in whichever key it exists
                        for k, v in data.items():
                            if isinstance(v, str) and '{PYTHON_PROBLEM}' in v:
                                data[k] = v.replace('{PYTHON_PROBLEM}', problem_text)
                        # Add separate key for test cases
                        data['test_cases'] = test_list
                        final_prompt = json.dumps(data, indent=2, ensure_ascii=False)
                    except Exception:
                        # Fallback if template is not valid JSON
                        processed_text = json.dumps(combined_text)[1:-1]
                        final_prompt = template_text.replace('{PYTHON_PROBLEM}', processed_text)
                elif 'xml' in fmt:
                    # Replace placeholder with ONLY problem text
                    processed_problem = escape_xml(problem_text)
                    final_prompt = template_text.replace('{PYTHON_PROBLEM}', processed_problem)

                    # Create XML for test cases
                    test_items = "\n".join([f"    <test_case>{escape_xml(t)}</test_case>" for t in test_list])
                    test_tag = f"<test_cases>\n{test_items}\n  </test_cases>"

                    # Insert test_cases tag after </task>
                    if "</task>" in final_prompt:
                        final_prompt = final_prompt.replace("</task>", f"</task>\n  {test_tag}")
                    else:
                        # Fallback if </task> is not found
                        final_prompt += f"\n{test_tag}"
                else:
                    # Plaintext or other
                    final_prompt = template_text.replace('{PYTHON_PROBLEM}', combined_text)

                # Write to file only if requested
                if generate_files:
                    filename = f"{sequence_number:04d}.txt"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(final_prompt)

                # Write to CSV
                writer.writerow({
                    'task_id': task_id,
                    'category_id': category_id,
                    'prompt': final_prompt,
                    'test_cases': test_cases_json,
                    'challenge_test_list': challenge_test_json
                })

                sequence_number += 1

    print(f"Generated {sequence_number - 1} prompts for {len(problems)} problem(s) in '{csv_file_path}'" + (f" and the '{output_dir}' folder." if generate_files else "."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate prompts from problems and templates.")
    parser.add_argument("--number_problem", type=int, default=None, help="Number of problems to process (default: all)")
    parser.add_argument("--files", action="store_true", help="Generate individual .txt files in the 'problems' folder (default: False)")
    args = parser.parse_args()

    generate_prompts(args.number_problem, args.files)
