#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

run_python_checks() {
  echo "[quality] Python syntax check"
  python3 -m compileall -q backends/python/api
}

run_json_checks() {
  echo "[quality] JSON consistency check"
  python3 - <<'PY'
import json
from pathlib import Path

json_files = [
    Path('docs/ROADMAP_TASKS.json'),
    Path('docs/ROADMAP_EXECUTION_STATUS.json'),
]
for path in json_files:
    json.load(path.open('r', encoding='utf-8'))
print('JSON validation OK')
PY
}

run_frontend_checks() {
  if ! command -v pnpm >/dev/null 2>&1; then
    echo "[quality] pnpm not found, frontend lint skipped"
    return 0
  fi
  echo "[quality] Frontend lint"
  pnpm --dir frontend install --frozen-lockfile
  pnpm --dir frontend lint
}

run_python_checks
run_json_checks
run_frontend_checks

echo "[quality] All baseline checks completed"
