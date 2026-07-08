import json
import os

folder = os.path.dirname(os.path.abspath(__file__))
durations = []

for fname in os.listdir(folder):
    if fname.endswith(".jsonl"):
        with open(os.path.join(folder, fname)) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if "duration_seconds" in obj:
                        durations.append(obj["duration_seconds"])
                except Exception:
                    continue

if durations:
    print("Min:", min(durations))
    print("Max:", max(durations))
    print("Average:", sum(durations) / len(durations))
else:
    print("No duration_seconds found.")
