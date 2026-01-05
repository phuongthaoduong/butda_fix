#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Being-Up-To-Date Assistant - Cleanup"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to kill processes on a specific port
kill_port() {
  local port=$1
  local pids=$(lsof -ti:$port 2>/dev/null || true)

  if [ -n "$pids" ]; then
    echo "Killing processes on port $port..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
    echo "✅ Port $port cleaned"
  else
    echo "✓ No process running on port $port"
  fi
}

# Stop services
echo "1/4 Stopping services..."
echo "----------------------------------------"
kill_port 8000  # Tool Server
kill_port 8001  # Backend
kill_port 5173  # Frontend
echo ""

# Clean up log files
echo "2/4 Cleaning log files..."
echo "----------------------------------------"
rm -f /tmp/backend*.log 2>/dev/null || true
rm -f /tmp/frontend*.log 2>/dev/null || true
rm -f /tmp/backend_*.log 2>/dev/null || true
rm -f /tmp/test*.json 2>/dev/null || true
rm -f /tmp/mp_*.json 2>/dev/null || true
rm -f /tmp/req*.json 2>/dev/null || true
rm -f /tmp/agenthub_test.log 2>/dev/null || true
echo "✅ Log files cleaned"
echo ""

# Clean Python cache
echo "3/4 Cleaning Python cache..."
echo "----------------------------------------"
cd "$ROOT_DIR"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Python cache cleaned"
echo ""

# Clean build artifacts
echo "4/4 Cleaning build artifacts..."
echo "----------------------------------------"
rm -rf "$ROOT_DIR/client/dist" 2>/dev/null || true
rm -rf "$ROOT_DIR/client/.vite" 2>/dev/null || true
rm -rf "$ROOT_DIR/server/.pytest_cache" 2>/dev/null || true
rm -rf "$ROOT_DIR/server/htmlcov" 2>/dev/null || true
rm -f "$ROOT_DIR/server/.coverage" 2>/dev/null || true
echo "✅ Build artifacts cleaned"
echo ""

echo "========================================"
echo "✅ Cleanup Complete!"
echo "========================================"
echo ""
echo "You can now run:"
echo "  ./scripts/start.sh"
echo ""
echo "To also remove dependencies (full reset):"
echo "  ./scripts/clean.sh --full"
echo ""

# Full cleanup option
if [ "${1:-}" = "--full" ]; then
  echo ""
  echo "========================================"
  echo "FULL CLEANUP - Removing Dependencies"
  echo "========================================"
  echo ""

  echo "Removing Python virtual environment..."
  rm -rf "$ROOT_DIR/server/.venv" 2>/dev/null || true
  echo "✅ Virtual environment removed"
  echo ""

  echo "Removing Node modules..."
  rm -rf "$ROOT_DIR/client/node_modules" 2>/dev/null || true
  rm -f "$ROOT_DIR/client/package-lock.json" 2>/dev/null || true
  echo "✅ Node modules removed"
  echo ""

  echo "========================================"
  echo "✅ Full Cleanup Complete!"
  echo "========================================"
  echo ""
  echo "Run ./scripts/install.sh to reinstall dependencies"
  echo ""
fi
