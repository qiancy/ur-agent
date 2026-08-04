#!/usr/bin/env bash
set -euo pipefail

echo "🔥 启动 Uni-Resource E2E 录屏演示..."
echo "请先确认后端 http://localhost:8000 与前端 http://localhost:5173 已启动。"

python3 -m pytest agents/tdd/playwright/test_demo_recording.py \
  -m recording \
  -v \
  --headed \
  --slowmo=500 \
  --reruns 1

