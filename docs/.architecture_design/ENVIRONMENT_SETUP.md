# Environment Setup Guide

## Overview
Simple environment configuration for local development. No complex deployment needed.

## Backend Environment (.env)
Create `server/.env` file:
```
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

# Research Agent Settings
MAX_RESULTS=10
SEARCH_TIMEOUT=15
SUMMARY_LENGTH=500
```

## Frontend Environment (.env)
Create `client/.env` file:
```
# API Configuration
VITE_API_URL=http://localhost:8001/api
VITE_APP_NAME=Research Agent
VITE_MAX_QUERY_LENGTH=500
VITE_REQUEST_TIMEOUT=30000
```

## Quick Setup Commands

### 1. Create Backend Environment
```bash
cd server
cat > .env << 'EOF'
ENVIRONMENT=development
PORT=8001
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
RATE_LIMIT_WINDOW_SECONDS=3600
RATE_LIMIT_MAX_REQUESTS=100
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379
MAX_QUERY_LENGTH=500
REQUEST_TIMEOUT_SECONDS=30
MAX_RESULTS=10
SEARCH_TIMEOUT=15
SUMMARY_LENGTH=500
EOF
```

### 2. Create Frontend Environment
```bash
cd ../client
cat > .env << 'EOF'
VITE_API_URL=http://localhost:8001/api
VITE_APP_NAME=Research Agent
VITE_MAX_QUERY_LENGTH=500
VITE_REQUEST_TIMEOUT=30000
EOF
```

## Update Backend to Use Environment Variables

Replace the hardcoded values in `server/main.py`:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", 8001))
HOST = os.getenv("HOST", "0.0.0.0")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 3600))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 100))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 3600))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", 500))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", 30))

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update Redis connection
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connected")
    except:
        redis_client = None
        print("⚠️  Redis not available, running without cache")

# Update validation
if len(request.query.strip()) < 3 or len(request.query) > MAX_QUERY_LENGTH:
    raise HTTPException(status_code=400, detail="Invalid query length")

# Update cache TTL
if redis_client:
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(response.dict()))

# Update uvicorn run
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=HOST, 
        port=PORT, 
        reload=(ENVIRONMENT == "development")
    )
```

## Update Frontend to Use Environment Variables

Update `client/src/App.jsx`:

```javascript
// Add at the top
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';
const MAX_QUERY_LENGTH = parseInt(import.meta.env.VITE_MAX_QUERY_LENGTH) || 500;
const REQUEST_TIMEOUT = parseInt(import.meta.env.VITE_REQUEST_TIMEOUT) || 30000;

// Update the fetch call
const response = await fetch(`${API_URL}/research`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ query }),
  signal: AbortSignal.timeout(REQUEST_TIMEOUT)
});

// Update query validation
if (!query.trim() || query.length > MAX_QUERY_LENGTH) {
  setError(`Query must be between 1 and ${MAX_QUERY_LENGTH} characters`);
  return;
}
```

## Environment Files Structure
```
research-agent-app/
├── server/
│   ├── .env              # Backend environment
│   ├── main.py
│   └── requirements.txt
└── client/
    ├── .env              # Frontend environment
    └── ...
```

## Environment Variables Reference

### Backend Variables
| Variable | Default | Description |
|----------|---------|-------------|
| ENVIRONMENT | development | Development/production mode |
| PORT | 8001 | Server port |
| HOST | 0.0.0.0 | Server host |
| CORS_ORIGINS | http://localhost:5173 | Allowed origins |
| RATE_LIMIT_WINDOW_SECONDS | 3600 | Rate limit time window |
| RATE_LIMIT_MAX_REQUESTS | 100 | Max requests per window |
| CACHE_TTL_SECONDS | 3600 | Cache TTL in seconds |
| REDIS_URL | redis://localhost:6379 | Redis connection URL |
| MAX_QUERY_LENGTH | 500 | Maximum query length |
| REQUEST_TIMEOUT_SECONDS | 30 | Request timeout |

### Frontend Variables
| Variable | Default | Description |
|----------|---------|-------------|
| VITE_API_URL | http://localhost:8001/api | Backend API URL (REQUIRED in production) |
| VITE_APP_NAME | Research Agent | App name |
| VITE_MAX_QUERY_LENGTH | 500 | Max query length |
| VITE_REQUEST_TIMEOUT | 30000 | Request timeout ms |

## Add python-dotenv to requirements.txt
Make sure to add to `server/requirements.txt`:
```
python-dotenv==1.0.0
```

Then reinstall dependencies:
```bash
cd server
pip install -r requirements.txt
```
## Zeabur Deployment Notes

- Services: deploy `server` (backend), `research-agent` (tool server), and `client` (frontend) as three services in one project.
- Order: Backend → Tool Server → Frontend.
- Frontend must define `VITE_API_URL` pointing to the backend domain in production; otherwise `client/src/App.tsx:32–149` guards and show a configuration error.
