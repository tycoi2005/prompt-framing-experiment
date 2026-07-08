import json
import re

d_path = 'problems/VNSchoolMathProblems2026/exam_problems.md'
j_path = 'problems/VNSchoolMathProblems.json'

with open(d_path, 'r', encoding='utf-8') as f:
    text = f.read()

problems = [p.strip() for p in re.findall(r'^\+ (.*?)$', text, re.MULTILINE)]

print(f"Extracted {len(problems)} problems from markdown.")

with open(j_path, 'r', encoding='utf-8') as f:
    existing = json.load(f)

# we can just print the first 5 not converted to see.
# The user wants to "add not exits problems", but LLM conversion is hard to do all 198 without an LLM API.
# Should we do string matching to see which are already in?
# We manually added 1,2,3 from specific and 4,5,6 are: lantern, radar, cone.
