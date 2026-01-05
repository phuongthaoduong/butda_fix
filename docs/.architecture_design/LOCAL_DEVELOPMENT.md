# Local Development Guide (MVP)

## Overview
This guide covers running the Research Agent application locally for MVP development. No Docker or deployment required - just run everything on your machine.

## Architecture (Local Setup)
```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend       │
│   (Vite Dev)    │◀────│   (FastAPI)     │
│   localhost:5173│     │   localhost:8001│
└─────────────────┘     └─────────────────┘
```

## Prerequisites
- Python 3.9+ 
- Node.js 18+
- Redis (optional, for caching)
- uv (Python package manager) - install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Quick Start

Use the repository scripts to install and start services.

```bash
# Install dependencies
./scripts/install.sh

# Start backend (FastAPI on 8001)
./scripts/start-backend.sh

# Start frontend (Vite on 5173)
./scripts/start-frontend.sh
```

### 2. Frontend (Vite/React)
Already configured in `client`. Use the start script above; Vite proxies `/api` to the backend.

## Optional: Redis Setup (for caching)
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Test Redis
redis-cli ping  # Should return PONG
```

## Development Workflow

### Start Services
Use the scripts in the project root.

### Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Next Steps

1. **Integrate Research Agent**: Replace the mock response in `main.py` with your actual research agent logic
2. **Add Error Handling**: Improve error messages and validation
3. **Enhance UI**: Add loading states, better styling, result formatting
4. **Add Tests**: Write unit tests for API endpoints
5. **Environment Variables**: Create `.env` files for configuration

## File Structure
```
research-agent-app/
├── server/
│   ├── .venv/                        # uv virtual environment
│   ├── main.py
│   ├── requirements.txt
│   └── pyproject.toml                # uv project config (optional)
└── client/
    ├── node_modules/
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Troubleshooting

### Port Already in Use
- Backend: Change `PORT` in `server/.env` or `app/core/config.py`
- Frontend: Change `server.port` in `client/vite.config.ts`

### Python Virtual Environment Issues
```bash
# Recreate venv with uv
rm -rf .venv
uv venv
uv pip install -r requirements.txt
```

### CORS Issues
- Ensure backend is running on port 8001
- Check CORS settings in `server/app/core/config.py`
- Verify proxy config in `client/vite.config.ts`
