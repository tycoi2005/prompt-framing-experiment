#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-root@207.154.209.169}"
REMOTE_DIR="${REMOTE_DIR:-~/thesis_runapis}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Copying run_apis files to ${REMOTE_HOST}:${REMOTE_DIR}/"
ssh "${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"
scp -q \
  "${SCRIPT_DIR}/run_api_matrix.py" \
  "${SCRIPT_DIR}/rerun_error_records.py" \
  "${SCRIPT_DIR}/problems.csv" \
  "${SCRIPT_DIR}/problems.math.csv" \
  "${SCRIPT_DIR}/.env.json" \
  "${REMOTE_HOST}:${REMOTE_DIR}/"

echo "Starting 3 model jobs in parallel on ${REMOTE_HOST}"
MODEL_LIST_FILE="$(mktemp)"
trap 'rm -f "${MODEL_LIST_FILE}"' EXIT
ssh "${REMOTE_HOST}" "cd ${REMOTE_DIR} && ${PYTHON_BIN} - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path('.env.json').read_text(encoding='utf-8'))
for model in cfg.get('models', []):
    print(model.get('name') or model.get('model_name'))
PY" > "${MODEL_LIST_FILE}"

while IFS= read -r model_name; do
  [ -n "${model_name}" ] || continue
  safe_name="$(printf '%s' "${model_name}" | tr -c 'A-Za-z0-9_.-' '-')"
  echo "Launching ${model_name}"
  ssh -n "${REMOTE_HOST}" "cd ${REMOTE_DIR} && mkdir -p logs pids results/python results/math && (nohup ${PYTHON_BIN} run_api_matrix.py --dataset both --model '${model_name}' > 'logs/${safe_name}.log' 2>&1 < /dev/null & echo \$! > 'pids/${safe_name}.pid')"
done < "${MODEL_LIST_FILE}"

echo "Remote jobs launched."
echo "Expected output files: 6 JSONL files under ${REMOTE_DIR}/results/{python,math}/"
echo "Check progress:"
echo "  ssh ${REMOTE_HOST} 'tail -f ${REMOTE_DIR}/logs/*.log'"
echo "Check running PIDs:"
echo "  ssh ${REMOTE_HOST} 'cat ${REMOTE_DIR}/pids/*.pid && ps -fp \$(cat ${REMOTE_DIR}/pids/*.pid)'"
