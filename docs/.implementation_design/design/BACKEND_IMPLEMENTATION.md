# Backend Implementation Design

## Overview

This document details the implementation approach for the FastAPI backend of the Being-Up-To-Date Assistant application. The backend serves as the intermediary between the frontend and the agent service, providing RESTful API endpoints, validation, and business logic.

## Project Structure

```
server/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── research.py
│   │   │   └── health.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── research_service.py
│   │   └── agent_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── research.py
│   │   └── schemas.py
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py
│       └── validators.py
├── main.py
├── requirements.txt
└── .env
```

## Implementation Steps

### 1. Environment Setup

Create `server/.env` with the following configuration:
```env
# Server Configuration
ENVIRONMENT=development
PORT=8001
HOST=0.0.0.0

# CORS Settings
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Rate Limiting
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_MAX_REQUESTS=100

# Cache Settings
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379

# Request Settings
MAX_QUERY_LENGTH=500
REQUEST_TIMEOUT_SECONDS=30

# Agent Service Settings
MAX_RESULTS=10
SEARCH_TIMEOUT=15
SUMMARY_LENGTH=500
```

### 2. Dependencies Setup

Create `server/requirements.txt`:
```txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
redis==5.0.1
httpx==0.25.2
pydantic==2.5.0
python-multipart==0.0.6
agenthub==latest
```

### 3. Core Configuration

Create `server/app/core/config.py`:
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 3600))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 100))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 3600))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", 500))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", 30))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 10))
SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", 15))
SUMMARY_LENGTH = int(os.getenv("SUMMARY_LENGTH", 500))
```

### 4. Data Models

Create `server/app/models/schemas.py`:
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ResearchRequest(BaseModel):
    query: str
    options: Optional[dict] = None

class SearchResult(BaseModel):
    id: str
    title: str
    url: str
    snippet: str
    publishedAt: datetime
    source: str
    relevanceScore: float

class Source(BaseModel):
    name: str
    url: str
    reliability: str
    type: str

class ResearchStatistics(BaseModel):
    totalResults: int
    processingTime: int
    searchTime: int
    summaryTime: int

class ResearchResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None

class ResearchData(BaseModel):
    query: str
    summary: str
    results: List[SearchResult]
    sources: List[Source]
    statistics: ResearchStatistics
    cached: bool
```

### 5. API Endpoints

Create `server/app/api/endpoints/research.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError
from app.models.schemas import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService
from app.core.config import MAX_QUERY_LENGTH

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    # Validate query
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")
    
    if len(request.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Query too long")
    
    try:
        research_service = ResearchService()
        result = await research_service.process_research(request.query, request.options)
        return ResearchResponse(success=True, data=result)
    except Exception as e:
        return ResearchResponse(
            success=False,
            error={
                "code": "INTERNAL_ERROR",
                "message": "An error occurred while processing your request",
                "details": {"error": str(e)}
            }
        )

@router.post("/research/sync")
async def sync_research(request: ResearchRequest):
    # Synchronous version for simpler integration
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query too short")
    
    if len(request.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Query too long")
    
    try:
        research_service = ResearchService()
        result = research_service.process_research_sync(request.query, request.options)
        return ResearchResponse(success=True, data=result)
    except Exception as e:
        return ResearchResponse(
            success=False,
            error={
                "code": "INTERNAL_ERROR",
                "message": "An error occurred while processing your request",
                "details": {"error": str(e)}
            }
        )
```

Create `server/app/api/endpoints/health.py`:
```python
from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }
```

### 6. Services Layer

Create `server/app/services/research_service.py`:
```python
import time
import json
import redis
from typing import Optional, Dict
from app.core.config import REDIS_URL, CACHE_TTL, MAX_RESULTS
from app.services.agent_service import AgentService

class ResearchService:
    def __init__(self):
        # Initialize Redis connection
        self.redis_client = None
        if REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                self.redis_client.ping()
            except:
                self.redis_client = None
    
    async def process_research(self, query: str, options: Optional[Dict] = None):
        start_time = time.time()
        
        # Check cache first
        cache_key = f"research:{query.lower()}"
        if self.redis_client:
            cached = self.redis_client.get(cache_key)
            if cached:
                result = json.loads(cached)
                result["cached"] = True
                result["statistics"]["processingTime"] = int((time.time() - start_time) * 1000)
                return result
        
        # Process with research agent
        agent_service = AgentService()
        search_start = time.time()
        search_results = await agent_service.search(query, options or {})
        search_time = int((time.time() - search_start) * 1000)
        
        # Format results
        formatted_results = self._format_results(search_results, query)
        formatted_results["statistics"]["searchTime"] = search_time
        formatted_results["statistics"]["processingTime"] = int((time.time() - start_time) * 1000)
        formatted_results["cached"] = False
        
        # Cache results
        if self.redis_client:
            self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(formatted_results))
        
        return formatted_results
    
    def process_research_sync(self, query: str, options: Optional[Dict] = None):
        start_time = time.time()
        
        # Check cache first
        cache_key = f"research:{query.lower()}"
        if self.redis_client:
            cached = self.redis_client.get(cache_key)
            if cached:
                result = json.loads(cached)
                result["cached"] = True
                result["statistics"]["processingTime"] = int((time.time() - start_time) * 1000)
                return result
        
        # Process with research agent
        agent_service = AgentService()
        search_start = time.time()
        search_results = agent_service.search_sync(query, options or {})
        search_time = int((time.time() - search_start) * 1000)
        
        # Format results
        formatted_results = self._format_results(search_results, query)
        formatted_results["statistics"]["searchTime"] = search_time
        formatted_results["statistics"]["processingTime"] = int((time.time() - start_time) * 1000)
        formatted_results["cached"] = False
        
        # Cache results
        if self.redis_client:
            self.redis_client.setex(cache_key, CACHE_TTL, json.dumps(formatted_results))
        
        return formatted_results
    
    def _format_results(self, search_results, query):
        # Format the results according to our schema
        return {
            "query": query,
            "summary": search_results.get("summary", "No summary available"),
            "results": search_results.get("results", []),
            "sources": search_results.get("sources", []),
            "statistics": {
                "totalResults": len(search_results.get("results", [])),
                "processingTime": 0,  # Will be filled later
                "searchTime": 0,      # Will be filled later
                "summaryTime": 0
            }
        }
```

Create `server/app/services/agent_service.py`:
```python
import agenthub as ah
from typing import Dict
from app.core.config import MAX_RESULTS, SEARCH_TIMEOUT

class AgentService:
    def __init__(self):
        # Load the research agent
        self.research_agent = ah.load_agent("agentplug/research-agent", external_tools=["web_search"])
    
    async def search(self, query: str, options: Dict):
        # Set search parameters
        max_results = options.get("maxResults", MAX_RESULTS)
        
        # Perform research using the agent
        try:
            result = self.research_agent.standard_research(query, max_results=max_results)
            return self._process_agent_result(result)
        except Exception as e:
            # Handle agent errors
            return {
                "summary": f"Error processing research: {str(e)}",
                "results": [],
                "sources": []
            }
    
    def search_sync(self, query: str, options: Dict):
        # Synchronous version for simpler integration
        try:
            result = self.research_agent.standard_research(query)
            return self._process_agent_result(result)
        except Exception as e:
            return {
                "summary": f"Error processing research: {str(e)}",
                "results": [],
                "sources": []
            }
    
    def _process_agent_result(self, result):
        # Process and format the agent result
        if isinstance(result, dict):
            return result
        else:
            # If result is not a dict, try to convert it
            return {
                "summary": str(result),
                "results": [],
                "sources": []
            }
```

### 7. Main Application Entry Point

Create `server/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import research, health
from app.core.config import CORS_ORIGINS, HOST, PORT, ENVIRONMENT

# Create FastAPI app
app = FastAPI(
    title="Being-Up-To-Date Assistant API",
    description="API for the Being-Up-To-Date Assistant application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Being-Up-To-Date Assistant API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=(ENVIRONMENT == "development")
    )
```

## Implementation Checklist

- [ ] Create project structure
- [ ] Set up environment configuration
- [ ] Install dependencies with uv
- [ ] Implement data models and schemas
- [ ] Create API endpoints for research and health
- [ ] Implement research service with caching
- [ ] Integrate with existing research agent
- [ ] Add validation and error handling
- [ ] Test API endpoints
- [ ] Document API with OpenAPI/Swagger

## Testing the Backend

1. Start the backend server:
   ```bash
   cd server
   uv run python main.py
   ```

2. Test the health endpoint:
   ```bash
   curl http://localhost:8001/api/health
   ```

3. Test the research endpoint:
   ```bash
   curl -X POST http://localhost:8001/api/research \
     -H "Content-Type: application/json" \
     -d '{"query": "Latest news about AI"}'
   ```

## Next Steps

1. Implement frontend integration
2. Add rate limiting
3. Enhance error handling
4. Add logging
5. Write unit tests
