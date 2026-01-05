#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Being-Up-To-Date Assistant - Starting Frontend"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/client"

if [ -f package.json ] && [ -d node_modules ]; then
  if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
  fi
  echo "Starting frontend (Vite) on http://localhost:5173"
  echo "Press Ctrl+C to stop"
  echo ""
  exec npm run dev -- --host 0.0.0.0 --port 5173
else
  echo "⚠️ Vite project not detected (missing package.json or node_modules)."
  echo "Starting static server for /client via Python on http://localhost:5173"
  echo "Press Ctrl+C to stop"
  echo ""
  exec python3 -m http.server 5173
fi
