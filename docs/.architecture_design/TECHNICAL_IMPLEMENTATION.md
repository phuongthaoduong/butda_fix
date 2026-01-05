# Technical Implementation Guide

## High-Level Project Structure

```
research-agent-app/
├── client/                           # Frontend React Application
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   │   ├── common/               # Shared components (Button, Input, etc.)
│   │   │   ├── research/             # Research-specific components
│   │   │   │   ├── ResearchForm.tsx
│   │   │   │   ├── ResearchResults.tsx
│   │   │   │   └── ResearchStatus.tsx
│   │   │   └── layout/               # Layout components (Header, Footer, etc.)
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useResearch.ts        # Research API hook
│   │   │   ├── useApi.ts             # Generic API hook
│   │   │   └── useErrorHandler.ts    # Error handling hook
│   │   ├── services/                 # API service layer
│   │   │   ├── api.ts                # Base API configuration
│   │   │   └── researchService.ts    # Research-specific API calls
│   │   ├── types/                    # TypeScript type definitions
│   │   │   ├── research.types.ts     # Research-related types
│   │   │   └── api.types.ts          # API response types
│   │   ├── utils/                    # Utility functions
│   │   │   ├── formatters.ts         # Data formatting utilities
│   │   │   └── validators.ts         # Input validation
│   │   ├── styles/                   # Global styles and themes
│   │   │   ├── globals.css
│   │   │   └── theme.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── server/                           # Backend FastAPI Application
│   ├── app/                          # Main application package
│   │   ├── api/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── research.py       # Research endpoints
│   │   │   │   └── health.py         # Health check endpoints
│   │   │   └── dependencies.py         # FastAPI dependencies
│   │   ├── core/                     # Core application logic
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Configuration management
│   │   │   ├── exceptions.py         # Custom exceptions
│   │   │   └── logging.py            # Logging configuration
│   │   ├── services/                   # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── research_service.py   # Research business logic
│   │   │   └── agent_service.py      # Agent management service
│   │   ├── models/                     # Data models
│   │   │   ├── __init__.py
│   │   │   ├── research.py           # Research data models
│   │   │   └── schemas.py            # Pydantic schemas
│   │   └── utils/                      # Utility functions
│   │       ├── __init__.py
│   │       ├── formatters.py         # Response formatting
│   │       └── validators.py         # Input validation
│   ├── tool_server.py                # Web search tool server
│   ├── main.py                       # FastAPI application entry point
│   ├── requirements.txt              # Python dependencies
│   ├── pyproject.toml                # uv project configuration (optional)
│   └── .python-version               # Python version specification (optional)
│
├── shared/                           # Shared utilities (optional)
│   ├── constants/                    # Shared constants
│   └── types/                        # Shared type definitions
│
├── tests/                            # Test suites
│   ├── client/                       # Frontend tests
│   │   ├── components/
│   │   ├── services/
│   │   └── integration/
│   └── server/                       # Backend tests
│       ├── unit/
│       ├── integration/
│       └── fixtures/
│
├── docs/                             # Documentation
│   ├── API.md                        # API documentation
│   ├── DEPLOYMENT.md                 # Deployment guide
│   └── DEVELOPMENT.md                # Development setup
│
├── scripts/                          # Utility scripts
│   ├── setup.sh                      # Initial setup script
│   ├── dev.sh                        # Development startup script
│   ├── deploy.sh                     # Deployment script
│   └── manage.sh                     # Process management script
│
├── .env.example                      # Environment variables template
├── .gitignore
└── README.md
```

## Module Architecture & Responsibilities

### Frontend Architecture (Client)

**Components Layer (`client/src/components/`)**
- **Common Components**: Reusable UI elements (buttons, inputs, cards, modals)
- **Research Components**: Domain-specific components for research functionality
- **Layout Components**: App-wide layout elements (header, footer, navigation)

**Services Layer (`client/src/services/`)**
- **api.ts**: Base HTTP client configuration, interceptors, error handling
- **researchService.ts**: Research-specific API calls, data transformation

**Hooks Layer (`client/src/hooks/`)**
- **useResearch.ts**: Research-specific state management and API integration
- **useApi.ts**: Generic API interaction patterns and caching
- **useErrorHandler.ts**: Centralized error handling and user feedback

**Types Layer (`client/src/types/`)**
- TypeScript interfaces for API responses, component props, and application state
- Ensures type safety across the frontend application

### Backend Architecture (Server)

**API Layer (`server/app/api/`)**
- **endpoints/**: RESTful endpoint definitions grouped by domain
- **dependencies.py**: FastAPI dependency injection (authentication, validation)

**Services Layer (`server/app/services/`)**
- **research_service.py**: Research business logic, agent orchestration
- **agent_service.py**: Agent management, tool coordination

**Core Layer (`server/app/core/`)**
- **config.py**: Environment-based configuration management
- **exceptions.py**: Custom exception classes for better error handling
- **logging.py**: Structured logging configuration

**Models Layer (`server/app/models/`)**
- **schemas.py**: Pydantic models for request/response validation
- **research.py**: Research-specific data models

### Tool Server Architecture
- **tool_server.py**: Independent process for web search tool
- Must be running for research agent to access web search capabilities

## Architectural Principles

### 1. Separation of Concerns
- **Frontend**: UI/UX, user interaction, presentation logic
- **Backend**: Business logic, API endpoints, agent orchestration
- **Tool Server**: External tool execution (web search)

### 2. Layered Architecture
- Each layer has specific responsibilities and clear interfaces
- Dependencies flow downward (presentation → business → data)
- Enables independent testing and development

### 3. Modular Design
- Components are self-contained and reusable
- Services encapsulate specific business domains
- Clear module boundaries prevent tight coupling

### 4. Type Safety
- TypeScript for frontend ensures compile-time error checking
- Pydantic models for backend provide runtime validation
- Shared type definitions maintain consistency

### 5. Scalability Considerations
- Stateless backend design enables horizontal scaling
- Tool server separation allows independent scaling
- Modular structure supports feature additions

## Key Design Decisions

### Frontend Decisions
- **Vite**: Fast build tool with excellent dev experience
- **React with TypeScript**: Type safety and component reusability
- **Custom Hooks**: Encapsulate complex logic and state management
- **Service Layer**: Centralized API communication and error handling

### Backend Decisions
- **FastAPI**: Modern, fast Python framework with automatic API docs
- **Pydantic**: Runtime data validation using Python type hints
- **Service Layer Pattern**: Business logic separation from API endpoints
- **Agent Integration**: Direct import of research agent for simplicity
- **uv**: Modern Python package and project management for fast dependency resolution

### Infrastructure Decisions
- **Tool Server Separation**: Independent process for external tools
- **No Database (MVP)**: Simplified architecture for initial release
- **Environment-based Config**: Flexible deployment across environments
- **No Docker (MVP)**: Direct process management for simplicity
- **Process-based Deployment**: Simple systemd or process manager deployment

## Modular Development Workflow

### Frontend Development
```bash
# Navigate to frontend
cd client

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Streaming Research (SSE)

- Endpoint: `GET /api/research/stream` streams progress updates and the final result.
- Chain of Thoughts (CoT): short, non-technical messages such as "Starting", "Searching", "Reading", "Thinking", "Writing".
- Disappears on completion: CoT is not persisted once the final answer is shown.

### Multiprocessing + Async

- Use the existing `AgentService.search_with_thoughts(query)` which yields async progress events from a separate process.
- This avoids blocking the FastAPI event loop while keeping implementation simple.

### Queue Draining During Streaming

- The streaming endpoint continuously consumes progress events and pushes them to SSE in real time.
- Final result is sent with a `complete` event that ends the stream.

### Error Handling

- If the agent fails mid-stream, the server sends an `error` event with a concise message.
- The client shows a simple error notice; no technical details.

### Browser SSE Timeout

- Send lightweight heartbeat comments `: heartbeat` at intervals to keep the connection alive on long queries.

### Backend Development
```bash
# Navigate to backend
cd server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Run tests
python -m pytest

# Start tool server (in separate terminal)
python tool_server.py
```

### Cross-Module Development
- Frontend and backend can be developed independently
- API contracts defined in OpenAPI/Swagger docs
- Mock services available for frontend development
- Type-safe communication between modules

### Testing Strategy
- **Unit Tests**: Individual component/service testing
- **Integration Tests**: Cross-module communication testing
- **End-to-End Tests**: Full user workflow testing
- **Contract Tests**: API interface validation

## Project Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Git
- uv (Python package manager) - install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Initial Project Structure (MVP - No Database)
```bash
research-agent-web/
├── client/                 # Frontend React app (Vite)
├── server/                 # Backend Python/FastAPI
├── .env                    # Environment variables
└── README.md              # Local development guide
```

## Frontend Implementation

### 1. Initialize React Project
```bash
cd client
npm create vite@latest . -- --template react-ts
npm install
```

### 2. Install Dependencies
```bash
npm install axios tailwindcss postcss autoprefixer
npm install -D @types/node
```

### 3. Core Components Structure
```typescript
// src/components/SearchInterface.tsx
interface SearchInterfaceProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };
  
  return (
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your research query..."
        maxLength={500}
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Searching...' : 'Research'}
      </button>
    </form>
  );
};
```

### 4. API Service (Backend Only)
```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

export interface ResearchRequest {
  query: string;
  options?: {
    maxResults?: number;
    timeframe?: 'recent' | 'week' | 'month' | 'year';
    includeSources?: boolean;
  };
}

export interface ResearchResponse {
  success: boolean;
  data: {
    query: string;
    summary: string;
    results: SearchResult[];
    sources: Source[];
    statistics: ProcessingStatistics;
  };
}

export const researchAPI = {
  // Client ONLY communicates with FastAPI backend - never directly with research agent
  async search(query: string, options?: ResearchRequest['options']): Promise<ResearchResponse> {
    const response = await axios.post(`${API_BASE_URL}/research`, {
      query,
      options
    });
    return response.data;
  }
};
```

## Security Architecture

### Server-Side Only Research Agent
The research agent runs exclusively on the server to ensure:
- **API Key Protection**: Research agent credentials never exposed to client
- **Rate Limiting**: Server controls research request frequency
- **Result Sanitization**: Server processes and formats results before client delivery
- **Error Handling**: Server-side errors don't expose internal details

### Client-Server Communication Flow
1. Client sends research query to FastAPI backend (`/api/research`)
2. Server validates query and calls research agent internally
3. Research agent processes query server-side only
4. Server formats results and returns to client
5. Client never has direct access to research agent

## Backend Implementation (Python/FastAPI)

### 1. Core Dependencies (MVP - Minimal)
```bash
cd server
uv venv  # Create virtual environment with uv
```python
# requirements.txt (MVP - No Redis/Database)
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
agenthub  # Research agent dependency
python-multipart==0.0.6
```

uv pip install -r requirements.txt  # Fast dependency installation
```

### 2. Main Application Structure
```python
# server/main.py (MVP)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import health, research
from app.core.config import CORS_ORIGINS, HOST, PORT, ENVIRONMENT

app = FastAPI(title="Research Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(research.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=(ENVIRONMENT == "development"),
    )
```

### 3. Integration with Research Agent

Backend integrates via `AgentService` (`server/app/services/agent_service.py`) and runs research in a separate process. No custom path hacks or separate tool server configuration required.

## Server-Side Integration Notes

Research runs entirely on the backend with `agenthub`. Clients never import or execute agent code.

## MVP Only - No Database Required

The MVP runs without any database. All data is processed server-side and returned directly to clients.

## Environment Configuration

### Frontend (.env)
```
VITE_API_URL=http://localhost:8001/api
VITE_APP_NAME=Research Agent
VITE_MAX_QUERY_LENGTH=500
VITE_REQUEST_TIMEOUT=30000
```

### Backend (.env)
```
ENVIRONMENT=development
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173
MAX_QUERY_LENGTH=500
REQUEST_TIMEOUT_SECONDS=30
```

## Development Workflow

### 1. Development Setup
```bash
# Install all dependencies
./scripts/install.sh

# Start services (separate terminals)
./scripts/start-backend.sh   # FastAPI on 8001
./scripts/start-frontend.sh  # Vite on 5173
# Tool server is optional for development and not required in production
```

### 2. Available Scripts
Frontend package.json:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

## Testing Strategy

### Unit Tests
```bash
# Frontend testing (if available)
cd client && npm test

# Backend testing (Python)
cd server && python -m pytest
```

## Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] Error handling verified
- [ ] Performance benchmarks met
- [ ] Security headers enabled
- [ ] CORS properly configured
- [ ] Tool server running (for web search functionality)

### Production Deployment
**Production checklist:**
- [ ] Environment variables set
- [ ] Frontend built and optimized
- [ ] Backend API configured for production
- [ ] Security headers enabled
- [ ] CORS properly configured
- [ ] Process manager configured (systemd, etc.)
- [ ] Log rotation configured
- [ ] SSL certificates installed

**Simple Deployment Process (No Docker):**
```bash
# 1. Frontend build
cd client
npm install
npm run build

# 2. Copy build to web server (nginx, Apache, etc.)
cp -r dist/* /var/www/html/

# 3. Backend setup
cd server
uv pip install -r requirements.txt

# 4. Start backend with process manager
# Option 1: systemd
sudo systemctl start research-backend

# Option 2: PM2
pm2 start main.py --name research-backend

# Option 3: Simple nohup
nohup uv run python main.py > backend.log 2>&1 &

# Tool server is not required for production
```

## Monitoring & Maintenance

### Health Checks
```bash
# Manual health check
curl https://api.research-agent.com/api/health
```

### Log Monitoring
- Application logs
- Error rates
- Response times

This implementation guide provides a complete roadmap for building the research agent web application while maintaining simplicity and focusing on essential features.
