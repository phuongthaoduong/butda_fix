#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Being-Up-To-Date Assistant - Starting Tool Server"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/tool-server"

if [ ! -d .venv ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting tool server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

exec python tool_server.py
