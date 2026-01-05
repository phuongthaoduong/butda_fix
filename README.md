# Being-Up-To-Date Assistant

AI-powered assistant for staying up-to-date, backed by AgentHub tools.

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm

## Quick Start

### 1. Installation

```bash
./scripts/install.sh
```

This installs:
- Backend Python dependencies (FastAPI, requirements.txt)
- Custom agenthub_sdk wheel package
- Frontend dependencies (React, Vite)

### 2. Configuration

Set up your environment variables (supply at least one LLM key):

```bash
cd server
cp .env.example .env
# Edit .env and add OPENAI_API_KEY or DEEPSEEK_API_KEY
```

### 3. Start Services

You need to run 3 services in separate terminals:

**Terminal 1 - Tool Server (Port 8000)**
```bash
./scripts/start-toolserver.sh
```

**Terminal 2 - Backend (Port 8001)**
```bash
./scripts/start-backend.sh
```

**Terminal 3 - Frontend (Port 5173)**
```bash
./scripts/start-frontend.sh
```

### 4. Access Application

Open your browser: http://localhost:5173

## Available Scripts

- `./scripts/install.sh` - Full installation
- `./scripts/start-toolserver.sh` - Start tool server on port 8000
- `./scripts/start-backend.sh` - Start backend API on port 8001
- `./scripts/start-frontend.sh` - Start frontend on port 5173
- `./scripts/clean.sh` - Stop all services and clean logs/cache
- `./scripts/clean.sh --full` - Full cleanup including dependencies

## Architecture

```
Browser (5173) → Backend (8001) → Agent Service (agenthub)
                                          ↓
                                   Tool Server (8000)
```

## Service Ports

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8001
  - Health check: http://localhost:8001/api/health
  - API docs: http://localhost:8001/docs
- **Tool Server**: http://localhost:8000 (internal)

## API Usage

```bash
curl -X POST http://localhost:8001/api/research \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Python programming?"}'
```

## Troubleshooting

**Port conflicts:**
```bash
# Kill processes on ports
./scripts/clean.sh
```

**Fresh install:**
```bash
./scripts/clean.sh --full
./scripts/install.sh
```

## Tech Stack

- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI, Python 3.12
- **Agent**: AgentHub SDK with web search tools
- **Tool Server**: MCP (Model Context Protocol)

## Zeabur Deployment

Use the provided `zbpack.backend.json`, `zbpack.toolserver.json`, and `zbpack.client.json` files to create three services inside a single Zeabur project so they can talk over the private network.

1. **Backend (FastAPI)**
   - Deploy with `zbpack.backend.json` (`app_dir: server`).
   - Build command: `pip install -r requirements.txt`; Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
   - Required env vars: `Deepseek_API_KEY` and optional `LOG_LEVEL`.
   - After Zeabur provisions networking, copy the private hostname (`Networking → Private`) for the frontend/tool server to use.
2. **Tool Server (research-agent)**
   - Deploy with `zbpack.toolserver.json` (`app_dir: research-agent`).
   - Build command: `pip install -r ../server/requirements.txt`; Start command: `python tool_server.py`.
   - Keep this service private (no public domain). Zeabur injects its hostname into other services as `TOOLSERVER_HOST`; the backend reads this variable to make internal calls.
3. **Frontend (Vite)**
   - Deploy with `zbpack.client.json` (`app_dir: client`, `output_dir: dist`).
   - Build command: `npm ci && npm run build`; Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`.
   - Set `VITE_API_URL=https://<backend-public-domain>` so the UI targets the FastAPI service. Attach a public Zeabur domain (or custom domain) for user access.

Make sure all three services live in the same Zeabur project for shared private networking and to allow the backend to reach the tool server without exposing it publicly.
