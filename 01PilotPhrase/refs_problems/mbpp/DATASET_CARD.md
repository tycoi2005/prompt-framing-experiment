# MBPP Dataset Card

**Source:** [Hugging Face - google-research-datasets/mbpp](https://huggingface.co/datasets/google-research-datasets/mbpp)

## Dataset Summary
The Mostly Basic Python Problems (MBPP) benchmark consists of around 1,000 crowd-sourced Python programming problems, designed to be solvable by entry level programmers. Each problem consists of a task description, a code solution, and 3 automated test cases.

## Data Structure
There are two versions: **full** (974 rows) and **sanitized** (427 rows).

### Fields
- `task_id`: Unique identifier for the task.
- `text` / `prompt`: Natural language description of the programming task.
- `code`: Canonical solution for the task.
- `test_list`: List of Python `assert` statements to verify the solution.
- `test_setup_code` / `test_imports`: Necessary code or imports to execute the tests.
- `challenge_test_list`: Additional challenging tests (full version only).

### Splits
- **Few-shot / Prompt:** Task IDs 1-10 (used for few-shot prompting, not training).
- **Test:** Task IDs 11-510.
- **Validation:** Task IDs 511-600.
- **Train:** Task IDs 601-974.

## Example Instance
```json
{
  "task_id": 1,
  "text": "Write a function to find the minimum cost path to reach (m, n) from (0, 0) for the given cost matrix cost[][] and a position (m, n) in cost[][].",
  "code": "R = 3\nC = 3\ndef min_cost(cost, m, n): \n\ttc = [[0 for x in range(C)] for x in range(R)] \n\ttc[0][0] = cost[0][0] \n\tfor i in range(1, m+1): \n\t\ttc[i][0] = tc[i-1][0] + cost[i][0] \n\tfor j in range(1, n+1): \n\t\ttc[0][j] = tc[0][j-1] + cost[0][j] \n\tfor i in range(1, m+1): \n\t\tfor j in range(1, n+1): \n\t\t\ttc[i][j] = min(tc[i-1][j-1], tc[i-1][j], tc[i][j-1]) + cost[i][j] \n\treturn tc[m][n]",
  "test_list": [
    "assert min_cost([[1, 2, 3], [4, 8, 2], [1, 5, 3]], 2, 2) == 8",
    "assert min_cost([[2, 3, 4], [5, 9, 3], [2, 6, 4]], 2, 2) == 12",
    "assert min_cost([[3, 4, 5], [6, 10, 4], [3, 7, 5]], 2, 2) == 16"
  ],
  "test_setup_code": "",
  "challenge_test_list": []
}
```

## Safety Warning
Execution of generated Python code should be done in a safe environment (sandboxed), as generated code could be harmful.
