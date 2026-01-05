# Phase 2 Testing Checklist

## Automated

- Backend
  - `cd server && pytest -q` – add tests that mock AgentService to return a deterministic payload; verify `/api/research` maps to frontend schema and sets `success: true`.
- Frontend
  - `cd client && npm run test` – mock API response and verify rendering of summary, results, sources, and statistics.

## Manual

### Prerequisites
- Ensure backend runs on `http://localhost:8001` and frontend on `http://localhost:5173`.
- If Redis is installed and configured (`REDIS_URL`), confirm it is running; otherwise proceed without cache.

### Backend
1. `./scripts/start-backend.sh` (port `8001`).
2. Run a research query:
   ```bash
   curl -X POST http://localhost:8001/api/research \
     -H "Content-Type: application/json" \
     -d '{"query":"best practices for python logging"}'
   ```
3. Verify response:
   - `success: true`
   - `data.summary` is a non-empty string
   - `data.results` and `data.sources` are arrays (may be empty depending on agent)
   - `data.statistics.processingTime` is present

### Frontend
1. `./scripts/start-frontend.sh` (port `5173`).
2. Open `http://localhost:5173`.
3. Enter a real query (e.g., “What is FastAPI?”) and submit.
4. Confirm:
   - Loading state shows while waiting
   - A summary appears
   - Results list renders with titles and external links opening in a new tab
   - Statistics show processing time; cache indicator may show `false` if cache not enabled

### Cache Behavior (Optional)
If Redis is configured (`server/.env` has `REDIS_URL`):
1. Run the same query twice.
2. Confirm the second response is faster and the UI indicates cache hit if implemented.

### Failure Modes
1. Stop Redis (if running) and retry queries; API should still return `success: true` or a structured error.
2. Temporarily disconnect network; confirm frontend shows an error message and allows retry.
