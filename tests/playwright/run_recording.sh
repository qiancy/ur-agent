#!/usr/bin/env bash
set -euo pipefail

echo "🔥 启动 Uni-Resource E2E 录屏演示（DEMO-DATA-02：liuming）..."
echo "请先确认后端 http://localhost:8000 与前端 http://localhost:5173 已启动。"

# 从 backend/.env（gitignored）读取 DEMO_LIUMING_PASSWORD 等未提交机密。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
while [[ "$REPO_ROOT" != "/" && ! -f "$REPO_ROOT/src/app.py" && ! -f "$REPO_ROOT/backend/src/app.py" ]]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done

if [[ -f "$REPO_ROOT/backend/src/app.py" ]]; then
  BACKEND_ROOT="$REPO_ROOT/backend"
elif [[ -f "$REPO_ROOT/src/app.py" ]]; then
  BACKEND_ROOT="$REPO_ROOT"
else
  echo "无法定位仓库根目录：未找到 src/app.py 或 backend/src/app.py" >&2
  exit 1
fi

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi
if [[ -f "$BACKEND_ROOT/.env" && "$BACKEND_ROOT" != "$REPO_ROOT" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$BACKEND_ROOT/.env"
  set +a
fi

export PYTHONPATH="$BACKEND_ROOT${PYTHONPATH:+:$PYTHONPATH}"

cd "$REPO_ROOT"

python3 -m pytest "$SCRIPT_DIR/test_demo_recording.py" \
  -m recording \
  -v \
  --headed \
  --slowmo=500 \
  --reruns 1
