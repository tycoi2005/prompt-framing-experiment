import json
with open('problems/VNSchoolMathProblems.json', 'r') as f:
    data = json.load(f)

task = data[-1]
code = task['code']
tests = task['test_list'] + task['challenge_test_list']

exec_globals = {}
exec(code, exec_globals)

for i, test in enumerate(tests):
    try:
        exec(test, exec_globals)
        print(f"Test {i} PASSED: {test}")
    except AssertionError:
        print(f"Test {i} FAILED: {test}")
    except Exception as e:
        print(f"Test {i} ERROR: {e}")
