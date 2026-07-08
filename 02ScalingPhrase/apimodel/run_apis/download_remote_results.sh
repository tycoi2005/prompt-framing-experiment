#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-root@207.154.209.169}"
REMOTE_DIR="${REMOTE_DIR:-~/thesis_runapis}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOCAL_DIR="${LOCAL_DIR:-${SCRIPT_DIR}/remote_downloads/${STAMP}}"

mkdir -p "${LOCAL_DIR}"

echo "Downloading remote outputs from ${REMOTE_HOST}:${REMOTE_DIR}"
echo "Local destination: ${LOCAL_DIR}"

REMOTE_TAR="/tmp/thesis_runapis_download_${STAMP}.tar.gz"
ssh "${REMOTE_HOST}" "cd ${REMOTE_DIR} && tar -czf ${REMOTE_TAR} \$(for d in results results_retry logs pids; do [ -e \"\$d\" ] && printf '%s ' \"\$d\"; done)"
scp -q "${REMOTE_HOST}:${REMOTE_TAR}" "${LOCAL_DIR}/remote_outputs.tar.gz"
ssh "${REMOTE_HOST}" "rm -f ${REMOTE_TAR}"
tar -xzf "${LOCAL_DIR}/remote_outputs.tar.gz" -C "${LOCAL_DIR}"

echo "Download complete."
echo "Summary:"
find "${LOCAL_DIR}" -type f -maxdepth 4 -print | sort
