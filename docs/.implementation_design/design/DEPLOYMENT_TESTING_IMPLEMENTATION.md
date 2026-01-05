# Deployment and Testing Implementation Design

## Overview

This document details the implementation approach for deploying and testing the Being-Up-To-Date Assistant application with a local-first mindset. It focuses on running the system directly on developer machines without Docker or Kubernetes. Containerization and orchestration can be explored later, but the immediate goal is a reliable, repeatable local workflow that supports iteration, testing, and handoff.

## Deployment Architecture (Local)

```
┌──────────────────────────────────────┐
│           Local Environment          │
├──────────────────────────────────────┤
│  Developer Workstation               │
│                                      │
│  ┌─────────────┐    HTTP/REST   ┌─────────────┐
│  │  Frontend   │ ◀────────────▶ │   Backend   │
│  │ (Vite/React)│                │  (FastAPI)  │
│  └─────────────┘                └─────────────┘
│          │                            │
│          ▼                            ▼
│   Browser DevTools          Redis (optional, local)
└──────────────────────────────────────┘
```

## Deployment Strategy

### 1. Development Environment

#### Local Development Setup
- **Frontend**: Vite development server with hot reloading
- **Backend**: Uvicorn development server with auto-reload
- **Database**: Local Redis instance for caching
- **Dependencies**: Managed with uv (backend) and npm (frontend)

#### Development Workflow
1. Clone repository
2. Set up environment variables
3. Install dependencies
4. Start services
5. Run tests
6. Make changes
7. Commit and push

#### Local Development Commands

**Backend Setup**:
```bash
cd server
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
cp .env.example .env
# Edit .env with local configuration
python main.py
```

**Frontend Setup**:
```bash
cd client
npm install
cp .env.example .env
# Edit .env with local configuration
npm run dev
```

> **Tip:** Set `REDIS_URL=` in the backend `.env` to skip caching during early development. Re-enable once you are ready to validate Redis locally.

### Manual Verification Checklist

- Backend responds at `http://127.0.0.1:8001/api/health`
- Frontend accessible at `http://127.0.0.1:5173`
- Submitting a query returns summarized results (mocked or live)
- Backend logs and errors remain visible in terminal
- Frontend hot reload reflects code changes instantly
- Optional: Redis caching confirmed when `REDIS_URL` points to local instance

## Zeabur Quick Setup

- Project: Create one Zeabur project with three services: `backend` (FastAPI), `tool-server` (MCP/AgentHub, private), `frontend` (static).
- Order: Backend → Tool Server → Frontend.
- Backend
  - Root: `server`
  - Build: `pip install --upgrade pip && pip install -r requirements.txt && pip install custom_packages/agenthub_sdk-0.1.4-py3-none-any.whl`
  - Start: `uvicorn main:app --host 0.0.0.0 --port ${PORT}`
  - Env: `ENVIRONMENT=production`, `HOST=0.0.0.0`, `PORT=${PORT}`, `CORS_ORIGINS=https://<frontend-domain>`
- Tool Server
  - Root: `research-agent`
  - Build: `pip install --upgrade pip && pip install -r ../server/requirements.txt && pip install ../server/custom_packages/agenthub_sdk-0.1.4-py3-none-any.whl`
  - Start: `python tool_server.py` (binds to `PORT` if provided)
  - Visibility: Private-only; reachable from backend via project networking
- Frontend
  - Root: `client`
  - Build: `npm ci && npm run build`
  - Output: `dist`
  - Env: `VITE_API_URL=https://<backend-domain>/api` (required in production; enforced by `client/src/App.tsx:32–149`)
- Verification
  - `curl https://<backend-domain>/api/health`
  - `curl -X POST https://<backend-domain>/api/research -H "Content-Type: application/json" -d '{"query":"hello"}'`

### Branching and Environments

| Environment | Purpose | How to Run |
|-------------|---------|------------|
| Local       | Daily development and testing | Run backend and frontend locally (commands above) |
| Preview (optional) | Shareable demo using local build artifacts | Manually deploy built assets to a shared VM or static host when needed |

At this stage, prioritize the local workflow. Formal staging and production environments can be defined once the MVP stabilizes. Containerization and orchestration should be treated as future enhancements rather than immediate requirements.

## Testing Strategy

### 1. Unit Testing

#### Backend Unit Tests
- **Framework**: pytest
- **Coverage**: >90% code coverage
- **Focus**: Individual functions and methods
- **Tools**: pytest, pytest-cov, pytest-mock

**Example Test**:
```python
# server/tests/test_research_service.py
import pytest
from app.services.research_service import ResearchService

def test_format_results():
    service = ResearchService()
    search_results = {
        "summary": "Test summary",
        "results": [{"id": "1", "title": "Test"}],
        "sources": [{"name": "Test Source"}]
    }
    
    formatted = service._format_results(search_results, "test query")
    
    assert formatted["query"] == "test query"
    assert formatted["summary"] == "Test summary"
    assert len(formatted["results"]) == 1
```

#### Frontend Unit Tests
- **Framework**: Jest and React Testing Library
- **Coverage**: >85% code coverage
- **Focus**: Component rendering and logic
- **Tools**: jest, @testing-library/react, @testing-library/jest-dom

**Example Test**:
```typescript
// client/src/components/__tests__/SearchForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import SearchForm from '../SearchForm';

test('renders search form with submit button', () => {
  const mockSubmit = jest.fn();
  render(<SearchForm onSubmit={mockSubmit} loading={false} />);
  
  expect(screen.getByPlaceholderText('Enter your research query...')).toBeInTheDocument();
  expect(screen.getByText('Submit Research')).toBeInTheDocument();
});

test('calls onSubmit when form is submitted', () => {
  const mockSubmit = jest.fn();
  render(<SearchForm onSubmit={mockSubmit} loading={false} />);
  
  const textarea = screen.getByPlaceholderText('Enter your research query...');
  const button = screen.getByText('Submit Research');
  
  fireEvent.change(textarea, { target: { value: 'Test query' } });
  fireEvent.click(button);
  
  expect(mockSubmit).toHaveBeenCalledWith('Test query');
});
```

### 2. Integration Testing

#### API Integration Tests
- **Framework**: pytest for backend, Jest for frontend
- **Focus**: End-to-end API workflows
- **Tools**: pytest, requests, axios-mock

**Example Test**:
```python
# server/tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"

def test_research_endpoint():
    response = client.post("/api/research", json={"query": "test"})
    assert response.status_code == 200
    # Add more assertions based on expected response structure
```

#### Frontend Integration Tests
```typescript
// client/src/__tests__/api.test.ts
import { researchApi } from '../services/api';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

test('submitResearch returns successful response', async () => {
  const mockResponse = {
    data: {
      success: true,
      data: {
        query: "test",
        summary: "Test summary",
        results: []
      }
    }
  };
  
  mockedAxios.post.mockResolvedValueOnce(mockResponse);
  
  const result = await researchApi.submitResearch({ query: "test" });
  
  expect(result.success).toBe(true);
  expect(result.data?.query).toBe("test");
});
```

### 3. End-to-End Testing

#### E2E Testing Framework
- **Tool**: Cypress
- **Focus**: User workflows and UI interactions
- **Coverage**: Critical user journeys

**Example Test**:
```javascript
// client/cypress/e2e/research_flow.cy.js
describe('Research Flow', () => {
  it('should submit a research query and display results', () => {
    cy.visit('/');
    
    cy.get('textarea[placeholder="Enter your research query..."]')
      .type('Latest developments in AI');
    
    cy.get('button').contains('Submit Research').click();
    
    cy.get('.loading-spinner', { timeout: 10000 }).should('not.exist');
    
    cy.get('.result-summary').should('contain.text', 'AI');
    cy.get('.search-results').should('exist');
  });
});
```

### 4. Performance Testing

#### Load Testing
- **Tool**: Locust or Artillery
- **Metrics**: Response time, throughput, error rate
- **Scenarios**: Concurrent users, peak load

**Example Load Test**:
```python
# load_test.py
from locust import HttpUser, task, between

class ResearchUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def research_query(self):
        self.client.post("/api/research", json={
            "query": "Latest developments in artificial intelligence"
        })
    
    def on_start(self):
        # Initialize user session if needed
        pass
```

### 5. Security Testing

#### Security Scanning
- **Tools**: OWASP ZAP, Bandit (Python), npm audit (JavaScript)
- **Checks**: Injection, XSS, CSRF, authentication

#### Vulnerability Assessment
```bash
# Backend security scan
bandit -r server/

# Frontend dependency audit
cd client && npm audit

# API security testing
zap-cli quick-scan http://localhost:8001
```

## Continuous Integration/Continuous Deployment (CI/CD)

### 1. CI Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    # Backend tests
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd server
        pip install uv
        uv pip install -r requirements.txt
    
    - name: Run backend tests
      run: |
        cd server
        pytest tests/
    
    # Frontend tests
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install frontend dependencies
      run: |
        cd client
        npm ci
    
    - name: Run frontend tests
      run: |
        cd client
        npm test
    
    # Security scanning
    - name: Run security scans
      run: |
        # Add security scanning commands
        echo "Security scanning"
```

### 2. CD Pipeline

Automated deployments are out of scope for the initial local-first phase. Instead, maintain a lightweight manual release checklist:

1. Ensure `main` passes CI (backend + frontend tests).
2. Generate backend build artifact (optional) using `python -m build` or similar.
3. Generate frontend build with `npm run build`.
4. Package artifacts (zip/tar) for hand-off or manual upload.
5. Update release notes in `CHANGELOG.md` (if available).
6. Tag the release in Git once the artifacts are verified.

> When the team is ready to revisit automation, this section can be expanded with Docker, container registries, or cloud deploy targets.

## Monitoring and Observability

### 1. Logging

#### Structured Logging
- **Format**: JSON logs with consistent structure
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Fields**: timestamp, level, service, message, context

**Example Log Entry**:
```json
{
  "timestamp": "2023-12-07T10:30:00Z",
  "level": "INFO",
  "service": "research-agent-backend",
  "message": "Research request processed successfully",
  "context": {
    "query": "AI developments",
    "processing_time_ms": 1250,
    "results_count": 10
  }
}
```

### 2. Metrics

#### Key Metrics to Monitor
- **API Response Time**: Average and 95th percentile
- **Error Rate**: Percentage of failed requests
- **Throughput**: Requests per second
- **Cache Hit Rate**: Percentage of cached responses
- **Resource Usage**: CPU, memory, disk I/O

#### Prometheus Metrics
```python
# server/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics definitions
REQUEST_COUNT = Counter('research_agent_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('research_agent_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('research_agent_active_connections', 'Active connections')
CACHE_HITS = Counter('research_agent_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('research_agent_cache_misses_total', 'Cache misses')
```

### 3. Alerting

#### Critical Alerts
- **High Error Rate**: >5% error rate for 5 minutes
- **Slow Response Time**: >2s average response time for 10 minutes
- **Service Unavailable**: Health check failures
- **Resource Exhaustion**: >90% CPU or memory usage

#### Alerting Rules
```yaml
# prometheus/alerts.yml
groups:
- name: research-agent-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(research_agent_requests_total{status="error"}[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 5% for the last 5 minutes"
```

## Backup and Recovery

### 1. Data Backup

#### Redis Backup
- **Frequency**: Daily snapshots
- **Retention**: 30 days of backups
- **Location**: Secure cloud storage
- **Verification**: Regular restore testing

#### Configuration Backup
- **Version Control**: All configuration in Git
- **Environment Variables**: Encrypted secrets management
- **Recovery Process**: Documented restore procedures

### 2. Disaster Recovery

#### Recovery Time Objective (RTO)
- **Target**: <30 minutes for partial outage
- **Target**: <2 hours for complete outage

#### Recovery Point Objective (RPO)
- **Target**: <1 hour of data loss

#### Recovery Procedures
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Determine scope of impact
3. **Communication**: Notify stakeholders
4. **Recovery**: Execute recovery plan
5. **Verification**: Confirm system functionality
6. **Post-mortem**: Document lessons learned

## Implementation Checklist

### Deployment
- [ ] Configure `.env` files for backend and frontend
- [ ] Document local startup instructions
- [ ] Validate backend health endpoint locally
- [ ] Validate frontend connection to backend
- [ ] Capture troubleshooting tips for common local issues
- [ ] Prepare manual deployment notes for future environments
- [ ] Outline roadmap for staging/production rollout (future)

### Testing
- [ ] Write unit tests for backend services
- [ ] Write unit tests for frontend components
- [ ] Implement integration tests for API endpoints
- [ ] Create end-to-end tests for user workflows
- [ ] Set up performance testing framework
- [ ] Implement security scanning
- [ ] Configure test coverage reporting

### Monitoring
- [ ] Implement structured logging
- [ ] Set up metrics collection
- [ ] Configure alerting rules
- [ ] Implement health checks
- [ ] Set up dashboard for key metrics
- [ ] Configure log aggregation

### Operations
- [ ] Document deployment procedures
- [ ] Create backup and recovery plan
- [ ] Implement disaster recovery procedures
- [ ] Set up monitoring and alerting
- [ ] Configure security measures
- [ ] Document operational runbooks

## Testing Commands

### Unit Testing
```bash
# Backend unit tests
cd server
pytest tests/ -v

# Frontend unit tests
cd client
npm test

# Test coverage
cd server
pytest tests/ --cov=app --cov-report=html
```

### Integration Testing
```bash
# Terminal 1: start backend
cd server
python main.py

# Terminal 2: run integration tests against running backend
cd server
pytest tests/integration/ -v

# Frontend integration tests
cd client
npm run test:integration
```

### End-to-End Testing
```bash
# Terminal 1: start backend
cd server
python main.py

# Terminal 2: start frontend
cd client
npm run dev

# Terminal 3: run E2E tests
cd client
npm run test:e2e

# Headless mode
npm run test:e2e:headless
```

### Performance Testing
```bash
# Install Locust
pip install locust

# Run load test
locust -f load_test.py --headless -u 100 -r 10
```

### Security Testing
```bash
# Backend security scan
bandit -r server/

# Frontend dependency audit
cd client
npm audit

# Fix vulnerabilities
npm audit fix
```

## Next Steps

1. Implement comprehensive monitoring and alerting
2. Set up automated backup procedures
3. Create detailed operational documentation
4. Implement advanced security measures
5. Optimize performance for production scale
6. Establish incident response procedures
7. Plan for future scalability and growth
## Zeabur Deployment Notes

- Deploy three services in one project: backend (FastAPI), tool server (MCP, private), and frontend (static).
- Deployment order: Backend → Tool Server → Frontend.
- In production, set `client/.env` with `VITE_API_URL=https://<backend-domain>/api` so the frontend can reach the API; otherwise the app enforces a configuration error in `client/src/App.tsx:32–149`.
