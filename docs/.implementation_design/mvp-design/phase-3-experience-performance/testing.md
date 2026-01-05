# Phase 3 Testing Checklist

## Automated

- Backend
  - Add tests for rate limiting: simulate multiple requests from same IP; expect 429 with structured error.
  - Validate sanitized queries (trimmed, collapsed spaces) and structured logging entries.
- Frontend
  - Test sorting/filtering interactions update rendered results.
  - Verify loading skeletons and progress messages appear during long requests.
  - Accessibility tests for modal/dialog focus and keyboard navigation.

## Manual

### Backend
1. Configure `server/.env`:
   - `RATE_LIMIT_MAX_REQUESTS=5`
   - `RATE_LIMIT_WINDOW_SECONDS=60`
2. `./scripts/start-backend.sh`.
3. Submit 6 requests quickly:
   ```bash
   for i in {1..6}; do curl -s -o /dev/null -w "%{http_code}\n" \
     -X POST http://localhost:8001/api/research \
     -H "Content-Type: application/json" \
     -d '{"query":"rate limit test"}'; done
   ```
4. Expect the last response code to be `429` and JSON with `error.code = RATE_LIMITED`.

### Frontend
1. `./scripts/start-frontend.sh`.
2. Open `http://localhost:5173`.
3. Enter a complex query and submit.
4. Confirm:
   - Skeletons render while loading
   - Summary and results appear organized into tabs or sections
   - Sorting and filtering controls update the visible list
   - FAQ/help is accessible and usable via keyboard

### Performance Profiling (Optional)
1. Use a simple loop to measure backend latency:
   ```bash
   for q in "python logging" "fastapi cors" "react vite"; do \
     time curl -s -X POST http://localhost:8001/api/research \
       -H "Content-Type: application/json" \
       -d "{\"query\":\"$q\"}" > /dev/null; \
   done
   ```
2. Record times and compare with baseline; aim for acceptable P95 under load.
