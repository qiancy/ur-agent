#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r agents/tdd/playwright/requirements.txt
python3 -m playwright install chromium

