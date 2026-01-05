# Research Agent Architecture Design

## Overview
A web-based research agent that searches the internet for the newest information based on user queries, then summarizes and provides intelligent answers. The system consists of a client (frontend) and server (backend) architecture. It features a "Chain of Thoughts" display to provide real-time, transparent progress updates that disappear once the final answer is ready, ensuring a clean and focused user experience.

## Core Requirements (KISS & YAGNI)
- User submits research queries (e.g., "News about H1B policy payment fee")
- System searches the web for latest relevant information
- System summarizes findings and provides comprehensive answers
- **Chain of Thoughts (CoT):** Real-time, non-technical progress updates (e.g., "Searching...", "Reading...") that vanish upon completion.
- Simple, focused functionality without unnecessary complexity
- User chooses a daily email time for a news digest (Gmail)
- User can save news items they care about

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│  Research       │
│   (Client)      │◀────│   (Server)      │◀────│  Agent Core     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       │                       ▼
        │                       │              ┌─────────────────┐
        │                       │              │   Web Search    │
        │                       │              │   APIs          │
        │                       │              └─────────────────┘
        ▼                       ▼                       
┌─────────────────┐     ┌─────────────────┐
│ Prefs & Saved   │     │ Notification    │
│ News UI         │     │ Scheduler       │
└─────────────────┘     └─────────────────┘
        │                       ▼
        ▼             ┌─────────────────┐
┌─────────────────┐   │ Email Sender    │
│ Preferences     │   │ (Gmail SMTP)    │
│ Store (JSON)    │   └─────────────────┘
└─────────────────┘           
        │
        ▼
┌─────────────────┐
│ Saved News      │
│ Store (JSON)    │
└─────────────────┘
```

## Notifications & Saved News (MVP)

- Frontend
  - Simple preferences form to choose daily email time (`HH:MM` local time)
  - Save/unsave button on each result; saved list view
- Backend
  - Minimal endpoints for preferences and saved news
  - Daily scheduler triggers digest generation at the configured time
- Email Delivery
  - Uses Gmail SMTP with app password
  - Credentials provided via environment variables; no secrets in code
- Storage (KISS)
  - Lightweight JSON files for `preferences` and `saved_news`
  - No database until needed

### Minimal Endpoints

- `GET /api/preferences/email-time` → `{ time: "HH:MM", timezone?: "string" }`
- `PUT /api/preferences/email-time` → `{ time: "HH:MM", timezone?: "string" }`
- `GET /api/news/saved` → `[ { id, title, url, source, savedAt } ]`
- `POST /api/news/saved` → `{ id, title, url, source }`
- `DELETE /api/news/saved/{id}` → `{ success: true }`
- `POST /api/notifications/send-now` → send digest immediately (preview/test)

## Frontend (Client) Design

### Technology Stack
- **Framework**: React.js with TypeScript
- **UI Library**: Tailwind CSS for styling
- **State Management**: React Context/Local State (KISS principle)
- **HTTP Client**: Fetch API or Axios
- **Build Tool**: Vite

### Key Components
1. **SearchInput**: Query input form
2. **ResultsDisplay**: Show search results and summaries
3. **ThoughtProcessDisplay**: Shows real-time "Chain of Thoughts" (e.g., "Searching...", "Analyzing") to keep users informed. Automatically disappears when the result is ready.
4. **LoadingState**: Minimal progress indicators (fallback)
5. **ErrorBoundary**: Error handling

### API Integration
- Primary endpoint: `GET /api/research/stream` (Server-Sent Events) for real-time CoT and final result
- Legacy endpoint: `POST /api/research` (Request/Response)
- Response (Stream): Sequence of thought events followed by the final result JSON.

## Backend (Server) Design

### Technology Stack
- **Runtime**: Python 3.9+
- **Framework**: FastAPI (modern, fast, async support)
- **API**: RESTful design with automatic OpenAPI docs
- **Research Core**: Integrate with existing research agent
- **Environment**: python-dotenv for configuration
- **AI/ML Libraries**: Native Python support for AI models, web scraping, NLP

### API Endpoints

#### GET /api/research/stream
**Purpose**: Stream research progress (Chain of Thoughts) and final result via Server-Sent Events (SSE).
**Query Param**: `query` (string)
**Response**: Stream of events:
- `event: thought` -> `{ message: "Searching web for..." }`
- `event: result` -> `{ summary: "...", sources: [...] }`

#### POST /api/research
**Purpose**: Process research queries (Non-streaming)
**Request Body**:
```json
{
  "query": "News about H1B policy payment fee",
  "options": {
    "maxResults": 10,
    "timeframe": "recent",
    "includeSources": true
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "News about H1B policy payment fee",
    "summary": "Comprehensive summary of findings...",
    "results": [
      {
        "title": "Article Title",
        "url": "https://example.com/article",
        "snippet": "Relevant excerpt...",
        "publishedAt": "2024-01-15T10:00:00Z"
      }
    ],
    "sources": [
      {
        "name": "Source Name",
        "url": "https://source.com",
        "reliability": "high"
      }
    ],
    "processingTime": 1250
  }
}
```

## Research Agent Core Integration

### Integration Strategy
The backend will integrate with the existing research agent (`/Users/phuongthaoduong/Project/research-agent`) as a module or service.

### Key Functions to Expose
```python
class ResearchAgent:
    async def search_and_summarize(self, query: str, options: dict = None) -> ResearchResult:
        """Search web and summarize findings"""
        pass
    
    def validate_query(self, query: str) -> bool:
        """Validate user query"""
        pass
    
    def format_results(self, results: list) -> list[FormattedResult]:
        """Format results for API response"""
        pass
```
```

### Error Handling
- Query validation
- Search API failures
- Timeout handling
- Rate limiting

## Data Flow
1. **User Input** → Frontend validation → Backend API (Stream Request)
2. **Backend** → Initialize Research Agent → [Stream: "Starting..."]
3. **Research Agent** → Web search → [Stream: "Searching sources..."]
4. **Research Agent** → Content extraction → [Stream: "Reading content..."]
5. **Research Agent** → Summarization → [Stream: "Analyzing..."]
6. **Final Result** → Backend → Frontend (CoT disappears, Result displayed)

## Security Considerations

### Input Validation
- Query length limits (max 500 characters)
- SQL injection prevention
- XSS protection
- Rate limiting per IP

### API Security
- CORS configuration
- Request size limits
- Timeout protection

## Performance Optimization

### Caching Strategy
- Redis for frequently searched queries (24h TTL)
- Browser caching for static assets
- CDN for frontend deployment

### Rate Limiting
- Per-user: 10 requests per minute
- Per-IP: 100 requests per hour

### Async Processing
- Long-running searches use background jobs
- WebSocket support for real-time updates (future enhancement)

## MVP Development (Local Only)

### Quick Start
- **Backend**: Python/FastAPI running on localhost:8001
- **Frontend**: React/Vite running on localhost:5173
- **No deployment needed** - everything runs locally
- **Optional Redis** for caching (can run without it)

### Local Development Setup
See [Local Development Guide](LOCAL_DEVELOPMENT.md) for step-by-step setup instructions.

## Cloud Deployment (Zeabur)

- Overview
  - Deploy three services inside one Zeabur project: `backend` (FastAPI), `tool-server` (MCP/AgentHub tool server), and `frontend` (static site)
  - Services share private networking and environment; `tool-server` remains private-only
  - Use environment variables for configuration; avoid secrets in code

- Backend Service (FastAPI)
  - Root directory: `server`
  - Build command: `pip install --upgrade pip && pip install -r requirements.txt && pip install custom_packages/agenthub_sdk-0.1.4-py3-none-any.whl`
  - Start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT}`
  - Environment variables:
    - `ENVIRONMENT=production`
    - `PORT=${PORT}` (provided by Zeabur)
    - `HOST=0.0.0.0`
    - `CORS_ORIGINS=https://<frontend-zeabur-domain>`
    - `OPENAI_API_KEY=...` (required for agent)

- Tool Server Service (MCP/AgentHub)
  - Root directory: `research-agent`
  - Build command: `pip install --upgrade pip && pip install -r ../server/requirements.txt && pip install ../server/custom_packages/agenthub_sdk-0.1.4-py3-none-any.whl`
  - Start command: `python tool_server.py`
  - Environment variables:
    - Optional: `PORT=${PORT}` if your platform requires binding to provided port (the tool server defaults to 8000); keep service private/unexposed

- Frontend Service (Static)
  - Root directory: `client`
  - Build command: `npm ci && npm run build`
  - Output directory: `dist`
  - Environment variables:
    - `VITE_API_URL=https://<backend-zeabur-domain>/api` (REQUIRED in production; the app enforces this in `client/src/App.tsx:32–149`)

- Networking
  - Frontend calls backend via `VITE_API_URL`
  - No direct access to agent or tool server from clients

-- Minimal Box Diagram (Zeabur)
```
┌───────────────┐     ┌───────────────┐      ┌───────────────┐
│ Frontend      │────▶│ Backend API   │─────▶│ Tool Server    │
│ (Static, CDN) │◀────│ (FastAPI)     │      │ (AgentHub MCP) │
└───────────────┘     └───────────────┘      └───────────────┘
                                   (private networking)
```

- YAGNI/KISS Decisions
  - Two services only; no monorepo build orchestration
  - Use `${PORT}` from Zeabur; no hardcoded ports
  - Static hosting for frontend; no SSR
  - Single `VITE_API_URL` env for client → backend routing

### Zeabur Deployment Order
- 1) Deploy Backend first
  - Confirm health at `/api/health` and docs at `/docs`
- 2) Deploy Tool Server second
  - Keep private; ensure backend can reach it via project networking
- 3) Deploy Frontend last
  - Set `VITE_API_URL` to the backend domain (e.g., `https://<backend-zeabur-domain>/api`)
  - Without `VITE_API_URL` in production, the app shows a configuration error (guard in `client/src/App.tsx:32–149`)

## Monitoring & Logging

### Key Metrics
- Search success rate
- Average response time
- Error rates by type
- User engagement metrics

### Logging
- Request/response logging
- Error tracking
- Performance metrics
- Simple analytics

## Future Enhancements (Post-MVP)
- User authentication and saved searches
- Advanced filtering and sorting
- Export functionality
- Mobile app
- Real-time collaboration
- Advanced analytics dashboard

## Technology Decisions (KISS/YAGNI)

### Why These Choices?
- **React + TypeScript**: Industry standard, type safety
- **FastAPI + Python**: Native AI/ML support, async performance, automatic API docs
- **REST API**: Simpler than GraphQL for this use case
- **No database initially**: Store everything in memory/cache
- **Single endpoint**: Reduces complexity
- **Static frontend hosting**: Cheaper and simpler than server-side rendering
- **Python ecosystem**: Rich AI/ML libraries (transformers, langchain, beautifulsoup, etc.)

## Project Structure
```
research-agent-web/
├── client/                 # Frontend React app
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── server/                 # Backend FastAPI app
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   ├── main.py
│   └── requirements.txt
├── shared/                 # Shared types/constants
└── docs/                   # Documentation
```

## Success Criteria
- Sub-second response time for cached queries
- 95%+ uptime
- User satisfaction with result quality
- Simple deployment process
- Minimal maintenance overhead

## Next Steps

1. **Review Architecture**: Ensure the design meets your requirements
2. **Set Up Local Development**: Follow the [Local Development Guide](LOCAL_DEVELOPMENT.md) for MVP setup
3. **Configure Environment**: Use the [Environment Setup Guide](ENVIRONMENT_SETUP.md) for configuration
4. **Integrate Research Agent**: Connect your existing research agent logic
5. **Deploy to Production**: Use the deployment guide when ready for production (optional)
