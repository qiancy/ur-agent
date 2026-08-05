#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 -m pip install -r "$SCRIPT_DIR/requirements.txt"
python3 -m playwright install chromium
