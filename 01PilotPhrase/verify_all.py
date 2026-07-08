"""Verify every task's canonical code passes its own test_list + challenge_test_list."""
import json, traceback

with open('problems/VNSchoolMathProblems.json', 'r') as f:
    data = json.load(f)

for task in data:
    tid = task['task_id']
    code = task['code']
    tests = task['test_list'] + task['challenge_test_list']
    
    exec_globals = {}
    try:
        exec(code, exec_globals)
    except Exception as e:
        print(f"Task {tid}: CODE EXEC ERROR: {e}")
        continue
    
    passed = 0
    failed_tests = []
    for i, test in enumerate(tests):
        try:
            exec(test, exec_globals)
            passed += 1
        except AssertionError:
            failed_tests.append((i, test, "AssertionError"))
        except Exception as e:
            failed_tests.append((i, test, str(e)))
    
    status = "PASS" if passed == len(tests) else "FAIL"
    print(f"Task {tid}: {status} ({passed}/{len(tests)})")
    for idx, t, err in failed_tests:
        print(f"  FAIL test[{idx}]: {t[:80]}... -> {err}")
