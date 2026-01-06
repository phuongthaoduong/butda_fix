# BUTDA - Being-Up-To-Date Assistant

A modern AI-powered research assistant that delivers concise, 3-minute news summaries on any topic through intelligent web search and content synthesis.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Components](#system-components)
- [Service Communication](#service-communication)
- [Why This Architecture?](#why-this-architecture)
- [Deployment](#deployment)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BUTDA System Map                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐         HTTP/HTTPS         ┌──────────────┐
│              │ ──────────────────────────> │              │
│   Browser    │  Port 5173 (Dev)           │   Frontend   │
│              │ < ─────────────────────────  │   (Client)   │
│              │     React UI / SSE           │   React+Vite │
└──────────────┘                            └──────┬───────┘
                                                   │
                                                   │ API Calls
                                                   │ (proxy in dev)
                                                   ↓
                                        ┌─────────────────────┐
                                        │                     │
                                        │   Backend Server    │
                                        │   (FastAPI)         │
                                        │   Port 8001          │
                                        │                     │
                                        │  ┌───────────────┐   │
                                        │  │ API Endpoints │   │
                                        │  │ - /api/health  │   │
                                        │  │ - /api/research│   │
                                        │  │ - /api/stream  │   │
                                        │  └───────┬───────┘   │
                                        │          │           │
                                        │  ┌───────▼────────┐  │
                                        │  │ AgentService   │  │
                                        │  │ (multiprocess) │  │
                                        │  └───────┬────────┘  │
                                        └──────────┼───────────┘
                                                   │
                                                   │ HTTP/WebSocket
                                                   │ Tool Calls
                                                   ↓
                                        ┌─────────────────────┐
                                        │  Tool Server         │
                                        │  (AgentHub)          │
                                        │  Port 8000           │
                                        │                     │
                                        │  ┌───────────────┐   │
                                        │  │ WebSearchTool │   │
                                        │  │ MCP Protocol  │   │
                                        │  └───────────────┘   │
                                        └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         Data Flow Diagram                            │
└─────────────────────────────────────────────────────────────────────┘

User Query
     │
     ▼
┌─────────────┐
│  Frontend   │ Display progress, sources, summary
│  (React)    │
└─────┬───────┘
      │
      │ POST /api/research
      ▼
┌─────────────┐
│  Backend    │ 1. Receive query
│  (FastAPI)  │ 2. Spawn AgentService (separate process)
└─────┬───────┘
      │
      │ multiprocessing.Queue
      ▼
┌─────────────────┐
│  AgentService   │ 1. Initialize AISuite client
│  (Process)      │ 2. Perform web search via Tool Server
│                 │ 3. Process search results
└─────┬───────────┘ 4. Generate summary using LLM
      │
      │ SSE Progress Updates
      ▼
┌─────────────┐
│  Frontend   │ Show: 🔎 Searching → 📖 Reading → ✅ Complete
└─────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      Technology Stack                                │
└─────────────────────────────────────────────────────────────────────┘

Frontend:
  • React 18.3.1        - UI Framework
  • TypeScript 5.5.3    - Type Safety
  • Vite 5.3.1          - Build Tool
  • Supabase JS        - Authentication

Backend:
  • FastAPI 0.115+      - Web Framework
  • Python 3.12+        - Runtime
  • Uvicorn            - ASGI Server
  • Redis 5.0+         - Caching (optional)
  • SSE-Starlette      - Server-Sent Events

Tool Server:
  • AgentHub SDK       - AI Agent Framework
  • Python 3.12+       - Runtime
  • WebSearchTool      - Search Integration

Infrastructure:
  • Zeabur             - Deployment Platform
  • Supabase          - Authentication & Database
```

---

## 🔧 System Components

### 1. Frontend (Client) - Port 5173
**Location:** `/client/`

**Purpose:** User interface for research queries and real-time progress tracking

**Responsibilities:**
- Render chat interface with message history
- Display real-time progress updates via Server-Sent Events (SSE)
- Show search sources and article discovery
- Present final research summary
- Handle user authentication (login/signup with email verification)
- Manage saved items and user settings

**Key Files:**
- `src/App.tsx` - Main application component
- `src/main.tsx` - Entry point
- `src/supabaseClient.ts` - Supabase client
- `vite.config.ts` - Vite configuration with API proxy

**Technology:**
```json
{
  "react": "^18.3.1",
  "typescript": "^5.5.3",
  "vite": "^5.3.1",
  "@supabase/supabase-js": "^2.39.0"
}
```

---

### 2. Backend Server - Port 8001
**Location:** `/server/`

**Purpose:** API gateway and research coordination

**Responsibilities:**
- Handle HTTP requests from frontend
- Spawn isolated AgentService processes (multiprocessing)
- Manage progress queues for real-time updates
- Cache research results (optional Redis)
- Coordinate between frontend and tool server

**API Endpoints:**
```
GET  /api/health          - Health check
POST /api/research        - Submit research query (JSON response)
GET  /api/research/stream - Submit research query (SSE streaming)
```

**Key Files:**
- `main.py` - FastAPI application entry
- `app/api/endpoints/` - API route handlers
- `app/services/agent_service.py` - Multiprocessing agent wrapper
- `app/services/research_service.py` - Research coordination
- `app/services/cache_client.py` - Redis caching
- `app/models/` - Pydantic schemas

**Technology:**
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.10.0
redis>=5.0.0
httpx>=0.27.0
sse-starlette>=2.1.0
agenthub_sdk (custom wheel)
```

---

### 3. Tool Server - Port 8000
**Location:** `/tool-server/`

**Purpose:** Provide AI agent tools (web search, MCP integration)

**Responsibilities:**
- Host AgentHub tool server
- Register WebSearchTool for agent usage
- Handle tool execution requests
- Provide MCP (Model Context Protocol) compatibility

**Key Files:**
- `app/main.py` - Tool server entry point
- `requirements.txt` - Only agenthub_sdk dependency

**Technology:**
```
agenthub_sdk (custom package)
```

---

## 🔄 Service Communication

### Request Flow (Research Query)

1. **User enters query in browser**
   ```
   "What are the latest developments in AI?"
   ```

2. **Frontend → Backend**
   ```typescript
   // Frontend (React)
   fetch('/api/research', {
     method: 'POST',
     body: JSON.stringify({ query: userQuery })
   })
   ```

3. **Backend spawns AgentService**
   ```python
   # Backend (FastAPI)
   from multiprocessing import Process, Queue

   result_queue = Queue()
   progress_queue = Queue()

   agent_process = Process(
       target=_run_agent_in_process,
       args=(query, result_queue, progress_queue)
   )
   agent_process.start()
   ```

4. **AgentService → Tool Server**
   ```python
   # AgentService (separate process)
   from agenthub import agent

   @agent.tool("web_search")
   def web_search(query: str) -> str:
       # Calls tool server at http://localhost:8000
       return search_results
   ```

5. **Progress updates via SSE**
   ```
   Backend → Frontend: Server-Sent Events
   Stages: 🔎 Searching → 📖 Reading → 📝 Summarizing → ✅ Complete
   ```

6. **Final response returned to frontend**
   ```json
   {
     "success": true,
     "data": {
       "summary": "Markdown formatted content...",
       "sources": [
         {
           "title": "Article Title",
           "url": "https://...",
           "snippet": "Preview..."
         }
       ]
     }
   }
   ```

---

## 💡 Why This Architecture?

### Three-Service Design Rationale

#### **Why Client + Backend + Tool Server?**

```
┌─────────────────────┬────────────────────────┬─────────────────────────┐
│     Component       │        Purpose          │          Benefit         │
├─────────────────────┼────────────────────────┼─────────────────────────┤
│ Frontend (React)    │ User Interface         │ Declarative UI, reactive │
│                     │ Authentication         │ state management         │
├─────────────────────┼────────────────────────┼─────────────────────────┤
│ Backend (FastAPI)   │ API Gateway            │ Async I/O, type safety   │
│                     │ Process Management     │ Easy scaling             │
├─────────────────────┼────────────────────────┼─────────────────────────┤
│ Tool Server         │ AI Agent Tools         │ Tool isolation,         │
│                     │ External Integrations  │ independent updates     │
└─────────────────────┴────────────────────────┴─────────────────────────┘
```

### **Pros**

✅ **Separation of Concerns**
- Frontend focuses on UX/UI
- Backend handles business logic
- Tool server provides external capabilities

✅ **Independent Development**
- Frontend team can work independently
- Backend changes don't affect UI
- Tool server can be updated separately

✅ **Technology Flexibility**
- Frontend: Best JS framework (React)
- Backend: Python for AI/ML ecosystem
- Tools: Any language/framework

✅ **Scalability**
- Scale each service independently
- Deploy tool server privately
- Add multiple tool servers

✅ **Fault Isolation**
- Tool server crash doesn't bring down backend
- Frontend errors don't affect research
- Process isolation prevents blocking

✅ **Security**
- Tool server can be internal-only
- Backend validates all requests
- Frontend never talks directly to tools

### **Cons**

❌ **Complexity**
- More services to manage
- Three deployment targets
- Inter-service communication overhead

❌ **Development Overhead**
- Need to run all three services locally
- More configuration files
- Debugging across services

❌ **Latency**
- Additional network hops
- Process spawning overhead (~100ms)
- Queue communication delay

❌ **Operational Cost**
- Three containers/services in production
- More monitoring points
- Higher infrastructure complexity

### **Why Multiprocessing for AgentService?**

**Critical for Linux compatibility:**

```python
# Without multiprocessing (BLOCKS on Linux):
async def research(query: str):
    agent.run()  # ❌ Blocks event loop
    # Browser hangs!

# With multiprocessing (WORKS everywhere):
def _run_agent_in_process(queue, query):
    agent.run()  # ✅ Isolated process

process = Process(target=_run_agent_in_process, args=(queue, query))
process.start()
# Backend stays responsive!
```

**Benefits:**
- ✅ Prevents event loop blocking
- ✅ Works on Linux servers
- ✅ Can terminate runaway agents
- ✅ True parallelism for multiple queries

**Trade-offs:**
- ❌ Process spawning overhead (~100ms)
- ❌ No shared memory (must use queues)
- ❌ More complex error handling

---

## 🚀 Deployment

### Zeabur Deployment

BUTDA uses Zeabur for cloud deployment with the following configuration:

#### **Service Configuration**

**1. Backend Server** (`zbpack.backend.json`)
```json
{
  "app_dir": "server",
  "build_command": "pip install -r requirements.txt && pip install agenthub_sdk",
  "start_command": "python start.py",
  "health_check_path": "/api/health"
}
```

**2. Tool Server** (`zbpack.toolserver.json`)
```json
{
  "app_dir": "tool-server",
  "build_command": "pip install -r requirements.txt",
  "start_command": "python app/main.py"
}
```

**3. Frontend** (`zbpack.client.json`)
```json
{
  "app_dir": "client",
  "build_command": "npm ci && npm run build",
  "start_command": "npm run preview",
  "output_dir": "dist"
}
```

### **Zeabur: Pros & Cons**

#### **Pros**

✅ **Simple Deployment**
- Git-based deployment (push to deploy)
- Automatic HTTPS
- Built-in load balancing
- Easy scaling

✅ **Developer Experience**
- Clean UI for service management
- Real-time logs
- Easy environment variable management
- Preview deployments

✅ **Cost Effective**
- Generous free tier
- Pay-per-use pricing
- No hidden infrastructure costs

✅ **Built-in Services**
- Supabase integration
- Easy domain configuration
- SSL certificates

#### **Cons**

❌ **Limited Control**
- Can't customize base Docker images
- Limited build configuration options
- Can't choose specific regions

❌ **Build Constraints**
- Fixed build timeouts
- Limited cache control
- Can't use custom build scripts

❌ **Platform Lock-in**
- Proprietary platform
- Migration would require reconfiguration
- Limited export options

### **Deployment Problems & Solutions**

#### **Problem 1: agenthub_sdk Installation**

**Issue:** `agenthub_sdk` is a custom wheel not in PyPI

**Solution:**
```json
// zbpack.backend.json
{
  "build_command": "pip install agenthub_sdk && pip install -r requirements.txt"
}

// zbpack.toolserver.json
{
  "build_command": "pip install agenthub_sdk"
}
```

**Alternative:** Host wheel file privately and install from URL

---

#### **Problem 2: Inter-Service Communication**

**Issue:** Tool server needs to be internal-only (not publicly accessible)

**Solution:**
- Deploy tool server as **private** service in Zeabur
- Backend communicates via internal Zeabur network
- Use environment variables for service URLs:

```bash
# Backend .env
TOOL_SERVER_URL=http://tool-server.zeabur.internal:8000
```

---

#### **Problem 3: Event Loop Blocking on Linux**

**Issue:** AgentHub blocking operations hang server on Linux

**Solution:** Multiprocessing architecture (see above)

```python
# Before (BLOCKS):
agent = AgentHub()
result = agent.search(query)  # ❌ Blocks

# After (NON-BLOCKING):
def run_agent(queue, query):
    agent = AgentHub()
    result = agent.search(query)  # ✅ In separate process
    queue.put(result)

process = Process(target=run_agent, args=(queue, query))
process.start()
```

---

#### **Problem 4: SSE Streaming Disconnections**

**Issue:** Server-Sent Events timeout or disconnect

**Solution:**
```python
# Configure SSE timeout
async def research_stream(request: Request):
    async with manager.connect() as sse:
        await manager.broadcast(sse, {"stage": "searching"})
        # Add keep-alive pings
        await asyncio.sleep(30)
        await manager.broadcast(sse, {"ping": "keepalive"})
```

---

#### **Problem 5: Frontend API Proxy in Production**

**Issue:** Vite proxy only works in development

**Solution:**
```typescript
// Development (vite.config.ts)
export default defineConfig({
  server: {
    proxy: {
      "/api": "http://localhost:8001"
    }
  }
})

// Production (use direct URL)
const API_BASE = import.meta.env.PROD
  ? "https://backend.zeabur.app"  // Zeabur URL
  : "/api";
```

---

#### **Problem 6: Environment Variable Management**

**Issue:** Different env vars for local vs production

**Solution:**
```bash
# Development (.env)
OPENAI_API_KEY=sk-...
TOOL_SERVER_URL=http://localhost:8000

# Production (Zeabur Dashboard)
OPENAI_API_KEY=sk-...
TOOL_SERVER_URL=https://tool-server.zeabur.internal
```

---

#### **Problem 7: Tool Server Directory Path**

**Issue:** Zeabur expects `app_dir` but tool server is in `tool-server/app`

**Solution:** Update `zbpack.toolserver.json`:
```json
{
  "app_dir": "tool-server",
  "start_command": "python app/main.py"
}
```

---

#### **Problem 8: Frontend Build Output Directory**

**Issue:** Default Vite output may not match Zeabur expectations

**Solution:** Configure in `vite.config.ts`:
```typescript
export default defineConfig({
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
```

---

#### **Problem 9: CORS Configuration**

**Issue:** Cross-origin requests blocked in production

**Solution:**
```bash
# Backend .env
CORS_ORIGINS=https://your-frontend.zeabur.app,https://custom.domain.com
```

---

#### **Problem 10: Service Startup Order**

**Issue:** Backend starts before tool server is ready

**Solution:** Add health checks and retry logic:
```python
import httpx
import time

def wait_for_tool_server(max_retries=30):
    for i in range(max_retries):
        try:
            response = httpx.get(f"{os.getenv('TOOL_SERVER_URL')}/health", timeout=5)
            if response.status_code == 200:
                return True
        except:
            time.sleep(1)
    return False

# Call in startup.py before starting app
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ for frontend
- **Python** 3.12+ for backend
- **Redis** (optional, for caching)
- **Supabase** account (for authentication)

### Local Development

#### 1. Installation

```bash
# Install backend dependencies
cd server
pip install -r requirements.txt
pip install agenthub_sdk  # Custom wheel

# Install tool server dependencies
cd ../tool-server
pip install -r requirements.txt

# Install frontend dependencies
cd ../client
npm install
```

Or use the provided script:
```bash
./scripts/install.sh
```

#### 2. Configuration

**Server** (`server/.env`):
```bash
# Required
OPENAI_API_KEY=sk-...  # or DEEPSEEK_API_KEY
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional

# Optional
REDIS_URL=redis://localhost:6379
PORT=8001
CORS_ORIGINS=http://localhost:5173
TOOL_SERVER_URL=http://localhost:8000
```

**Client** (`client/.env`):
```bash
VITE_API_URL=http://localhost:8001/api
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

#### 3. Start Services

**Terminal 1 - Tool Server:**
```bash
cd tool-server
python app/main.py
# Runs on port 8000
```

**Terminal 2 - Backend:**
```bash
cd server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# Runs on port 8001
```

**Terminal 3 - Frontend:**
```bash
cd client
npm run dev
# Runs on port 5173
```

Or use the provided scripts:
```bash
./scripts/start-toolserver.sh
./scripts/start-backend.sh
./scripts/start-frontend.sh
```

#### 4. Access the Application

Open browser to: `http://localhost:5173`

### Production Deployment (Zeabur)

1. **Push code to Git repository** (GitHub/GitLab)
2. **Create Zeabur project** and link repository
3. **Create three services:**
   - Backend → Deploy `server/` directory
   - Tool Server → Deploy `tool-server/` directory (private)
   - Frontend → Deploy `client/` directory
4. **Configure environment variables** in Zeabur dashboard
5. **Set up inter-service communication** (internal network)
6. **Configure custom domains** (optional)

---

## 🔑 Environment Variables

### Backend (`server/.env`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key | - |
| `DEEPSEEK_API_KEY` | Yes* | DeepSeek API key | - |
| `OPENAI_BASE_URL` | No | Custom OpenAI endpoint | - |
| `REDIS_URL` | No | Redis connection URL | - |
| `PORT` | No | Backend port | 8001 |
| `HOST` | No | Backend host | 0.0.0.0 |
| `CORS_ORIGINS` | No | Allowed CORS origins | - |
| `TOOL_SERVER_URL` | Yes | Tool server URL | http://localhost:8000 |

*One of `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` is required.

### Frontend (`client/.env`)

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `VITE_API_URL` | No | Backend API URL | http://localhost:8001/api |
| `VITE_SUPABASE_URL` | Yes | Supabase project URL | - |
| `VITE_SUPABASE_ANON_KEY` | Yes | Supabase anon key | - |

---

## 📚 API Documentation

### POST /api/research

Submit a research query and receive JSON response.

**Request:**
```http
POST /api/research
Content-Type: application/json

{
  "query": "What are the latest developments in AI?",
  "options": {
    "max_results": 10,
    "include_sources": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "What are the latest developments in AI?",
    "summary": "# Latest Developments in AI\n\n## 1. Large Language Models\n...",
    "sources": [
      {
        "title": "Breaking: GPT-5 Rumors",
        "url": "https://example.com/article1",
        "snippet": "Industry insiders suggest..."
      }
    ],
    "statistics": {
      "totalResults": 10,
      "processingTime": 1500,
      "cached": false
    }
  }
}
```

### GET /api/research/stream

Submit a research query and receive real-time progress via SSE.

**Request:**
```http
GET /api/research/stream?query=AI%20developments
```

**SSE Events:**
```
data: {"stage": "🔎 Searching", "message": "Finding relevant articles..."}

data: {"stage": "📖 Reading", "sources": [...]}

data: {"stage": "✅ Complete", "summary": "..."}
```

---

## 🛠️ Troubleshooting

### AgentService hangs on Linux

**Symptom:** Browser freezes when submitting query

**Cause:** AgentHub blocking operations in async context

**Solution:** Ensure multiprocessing is used (see backend/app/services/agent_service.py)

### Tool server connection refused

**Symptom:** "Connection refused" errors in backend

**Cause:** Tool server not running or wrong URL

**Solution:**
```bash
# Check tool server is running
curl http://localhost:8000/health

# Check TOOL_SERVER_URL in .env
echo $TOOL_SERVER_URL
```

### CORS errors in browser

**Symptom:** "Access-Control-Allow-Origin" errors

**Cause:** Frontend origin not allowed

**Solution:**
```bash
# Add to server/.env
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### agenthub_sdk not found

**Symptom:** "ModuleNotFoundError: No module named 'agenthub'"

**Cause:** Custom wheel not installed

**Solution:**
```bash
pip install agenthub_sdk
```

---

## 📁 Project Structure

```
butda_fix/
├── client/                    # React Frontend
│   ├── src/
│   │   ├── App.tsx          # Main component
│   │   ├── main.tsx         # Entry point
│   │   ├── supabaseClient.ts
│   │   └── App.css
│   ├── package.json
│   ├── vite.config.ts
│   └── .env                 # Frontend env vars
│
├── server/                   # FastAPI Backend
│   ├── main.py              # FastAPI app
│   ├── start.py             # Startup script
│   ├── app/
│   │   ├── api/endpoints/   # API routes
│   │   ├── core/            # Config
│   │   ├── models/          # Schemas
│   │   └── services/        # Business logic
│   ├── requirements.txt
│   └── .env                 # Backend env vars
│
├── tool-server/             # AgentHub Tool Server
│   ├── app/main.py
│   └── requirements.txt
│
├── scripts/                 # Utility scripts
│   ├── start-toolserver.sh
│   ├── start-backend.sh
│   ├── start-frontend.sh
│   ├── install.sh
│   └── clean.sh
│
├── zbpack.backend.json      # Zeabur config - backend
├── zbpack.toolserver.json   # Zeabur config - tool server
├── zbpack.client.json       # Zeabur config - frontend
└── README.md
```

---

## 🏆 Key Features

- ✅ **Real-time Progress** - Watch as BUTDA searches, reads, and summarizes
- ✅ **Source Integration** - Click through to original articles
- ✅ **Smart Caching** - Redis-backed result caching
- ✅ **Email Verification** - Secure signup with Supabase Auth
- ✅ **Dark Mode** - Easy on the eyes
- ✅ **Save & Export** - Save research and export to Word/PDF
- ✅ **User Profiles** - Track preferences and interesting topics
- ✅ **Multiprocessing** - Non-blocking agent execution

---

## 📄 License

This project is proprietary software.

---

## 👥 Support

For issues or questions, please contact the development team.
