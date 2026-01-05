# API Specification

## Base URL
- Development: `http://localhost:8001/api`
- Production (Zeabur): `https://<backend-zeabur-domain>/api`

## API Documentation
FastAPI automatically generates interactive API documentation:
- Swagger UI: `https://<backend-zeabur-domain>/docs`
- ReDoc: `https://<backend-zeabur-domain>/redoc`

## Deployment Order and Client Configuration
- Deploy backend API first, then tool server, then frontend.
- In production, set `client/.env` with `VITE_API_URL=https://<backend-zeabur-domain>/api` so the frontend can reach the API; otherwise the app throws a configuration error (guard implemented in `client/src/App.tsx:32–149`).

## Authentication
No authentication required for MVP (KISS principle). Rate limiting will handle abuse prevention.

## Endpoints

### GET /research/stream

Description: Stream real-time progress (Chain of Thoughts) and the final result using Server-Sent Events (SSE).

Request:
```
GET /api/research/stream?query=string
```

Streamed Events:
- `event: progress` with data `{ "stage": "starting|searching|reading|thinking|writing", "message": "string" }`
- `event: complete` with data `{ "stage": "complete", "success": true, "data": { ...final result... } }`
- `event: error` with data `{ "stage": "error", "message": "string", "error": "string" }`
- Heartbeat comments to keep the connection alive: `: heartbeat\n\n`

Notes:
- Progress events are short, plain-language updates for readability.
- On completion, progress messages stop and only the final result remains on screen.

### POST /research

**Description**: Submit a research query and receive summarized results

**Request Headers**:
```
Content-Type: application/json
Accept: application/json
```

**Request Body**:
```json
{
  "query": "string (required, max 500 characters)",
  "options": {
    "maxResults": "number (optional, default: 10, max: 20)",
    "timeframe": "string (optional, enum: ['recent', 'week', 'month', 'year'], default: 'recent')",
    "includeSources": "boolean (optional, default: true)",
    "language": "string (optional, default: 'en')"
  }
}
```

**Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "query": "string",
    "summary": "string (comprehensive summary)",
    "results": [
      {
        "id": "string (unique identifier)",
        "title": "string",
        "url": "string (valid URL)",
        "snippet": "string (relevant excerpt, max 500 chars)",
        "publishedAt": "string (ISO 8601 datetime)",
        "source": "string (domain name)",
        "relevanceScore": "number (0-1)"
      }
    ],
    "sources": [
      {
        "name": "string",
        "url": "string (valid URL)",
        "reliability": "string (enum: ['high', 'medium', 'low'])",
        "type": "string (enum: ['news', 'academic', 'blog', 'official'])"
      }
    ],
    "statistics": {
      "totalResults": "number",
      "processingTime": "number (milliseconds)",
      "searchTime": "number (milliseconds)",
      "summaryTime": "number (milliseconds)"
    },
    "cached": "boolean"
  }
}
```

**Error Responses**:

**400 Bad Request**:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Query is required and must be less than 500 characters",
    "details": {
      "field": "query",
      "provided": "actual value"
    }
  }
}
```

**429 Too Many Requests**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retryAfter": 60
    }
  }
}
```

**500 Internal Server Error**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An error occurred while processing your request",
    "details": {
      "requestId": "unique-request-id"
    }
  }
}
```

**503 Service Unavailable**:
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service temporarily unavailable. Please try again later.",
    "details": {
      "retryAfter": 300
    }
  }
}
```

### GET /health

**Description**: Health check endpoint for monitoring

**Success Response (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0.0",
  "uptime": 3600
}
```

### GET /preferences/email-time

**Description**: Retrieve the configured daily email time

**Success Response (200 OK)**:
```json
{
  "time": "08:00",
  "timezone": "local"
}
```

### PUT /preferences/email-time

**Description**: Set the daily email time

**Request Body**:
```json
{
  "time": "HH:MM",
  "timezone": "local" // optional
}
```

**Success Response (200 OK)**:
```json
{ "success": true }
```

### GET /news/saved

**Description**: List saved news items

**Success Response (200 OK)**:
```json
{
  "items": [
    {
      "id": "string",
      "title": "string",
      "url": "string",
      "source": "string",
      "savedAt": "2025-01-01T09:00:00Z"
    }
  ]
}
```

### POST /news/saved

**Description**: Save a news item

**Request Body**:
```json
{
  "id": "string",
  "title": "string",
  "url": "string",
  "source": "string"
}
```

**Success Response (201 Created)**:
```json
{ "success": true }
```

### DELETE /news/saved/{id}

**Description**: Remove a saved news item

**Success Response (200 OK)**:
```json
{ "success": true }
```

### POST /notifications/send-now

**Description**: Send a digest immediately (preview/test)

**Request Body (optional)**:
```json
{ "limit": 5 }
```

**Success Response (200 OK)**:
```json
{ "success": true, "sent": true }
```

## Rate Limiting
- **Per IP**: 100 requests per hour
- **Per user session**: 10 requests per minute (if user tracking implemented)
- **Burst allowance**: 5 requests per second

## Caching
- **Response caching**: 1 hour for identical queries
- **CDN caching**: 30 minutes for static responses
- **Browser caching**: 5 minutes for GET requests

## Error Handling
All errors follow consistent format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {} // Optional additional context
  }
}
```

## Validation Rules
- Query length: 3-500 characters
- No HTML/JavaScript allowed in queries
- Rate limiting per IP
- Timeout: 30 seconds per request
- Maximum concurrent requests: 5 per IP

## Performance Targets
- Response time: <2 seconds for cached queries, <10 seconds for new searches
- Availability: 99.9% uptime
- Success rate: >95% for valid requests
- Error rate: <5% for all requests
