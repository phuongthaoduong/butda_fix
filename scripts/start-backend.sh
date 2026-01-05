#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Being-Up-To-Date Assistant - Starting Backend"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/server"

if [ ! -d .venv ]; then
  echo "❌ Virtual environment not found."
  echo "Run: ./scripts/install.sh"
  exit 1
fi

source .venv/bin/activate

echo "Starting backend on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""

exec uvicorn main:app --reload --host 0.0.0.0 --port 8001
