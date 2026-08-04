#!/usr/bin/env bash
set -euo pipefail

echo "🔥 启动 Uni-Resource E2E 录屏演示（DEMO-DATA-02：liuming）..."
echo "请先确认后端 http://localhost:8000 与前端 http://localhost:5173 已启动。"

# 从仓库根目录 .env（gitignored）读取 DEMO_LIUMING_PASSWORD 等未提交机密。
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

python3 -m pytest agents/tdd/playwright/test_demo_recording.py \
  -m recording \
  -v \
  --headed \
  --slowmo=500 \
  --reruns 1

