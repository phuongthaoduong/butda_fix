# Phase 1 Testing Checklist

## Automated

- Backend
  - `cd server && pytest` – verifies `/api/health` and `/api/research` responses match the stub contract.
- Frontend
  - `cd client && npm run test` – exercises the `SearchForm` validation and submission flow.

## Manual

### Backend
1. `./scripts/install.sh`
2. `cp server/.env.example server/.env`
3. `./scripts/start-backend.sh`
4. In another terminal: `curl -X POST http://localhost:8001/api/research -H "Content-Type: application/json" -d '{"query":"Phase 1 smoke test"}'`.
5. Verify the response contains `summary`, `results`, `sources`, and `cached: false`.

### Frontend
1. `./scripts/install_frontend.sh`.
2. `cp client/.env.example client/.env`.
3. `./scripts/start_frontend.sh`.
4. Browse to `http://localhost:5173`.
5. Enter any query text and submit.
6. Confirm:
   - Loading spinner appears briefly.
   - Stub summary and results render.
   - `Cached` badge is not shown (false).
   - Reset button clears the form and hides results.

### Additional Checks
- Inspect browser network tab to confirm a single POST request to `/api/research`.
- Verify console/log output in backend terminal includes query and latency details.
- Try leaving the field empty and ensure the submit button remains disabled.
