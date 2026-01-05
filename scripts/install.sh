#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "Being-Up-To-Date Assistant - Full Installation"
echo "========================================"
echo ""

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Install Backend
echo "1/2 Installing Backend..."
echo "----------------------------------------"
cd "$ROOT_DIR/server"

if [ ! -d .venv ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install custom_packages/agenthub_sdk-0.1.4-py3-none-any.whl

echo "✅ Backend dependencies installed"
echo ""

# Install Frontend
echo "2/2 Installing Frontend..."
echo "----------------------------------------"
cd "$ROOT_DIR/client"

npm install || {
  echo "❌ Failed to install frontend dependencies"
  exit 1
}

echo "✅ Frontend dependencies installed"
echo ""

echo "========================================"
echo "✅ Installation Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  ./scripts/start.sh"
echo ""
echo "Or start services separately:"
echo "  ./scripts/start-backend.sh"
echo "  ./scripts/start-frontend.sh"
echo ""
