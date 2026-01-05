# Phase 4 Testing Checklist

## Automated

- Backend
  - Run `pytest -q` with coverage; enforce threshold (e.g., 80%+). Include unit and integration suites.
  - Security scan: `bandit -r server` and `pip-audit` (optional).
- Frontend
  - Unit tests for components and hooks; integration tests with MSW.
  - E2E tests via Playwright/Cypress hitting dev backend.
  - Accessibility audit with axe/Lighthouse.

## Manual

### Release Dry Run
1. Build frontend: `cd client && npm run build`.
2. Package backend: ensure `requirements.txt` and start command are correct.
3. Start services and perform smoke tests:
   - `./scripts/start-backend.sh`
   - `./scripts/start-frontend.sh`
4. Verify:
   - API docs accessible: `http://localhost:8001/docs`
   - Frontend query flow works end-to-end
   - Logs are structured and include request IDs

### Observability
1. Check metrics endpoint if enabled.
2. Confirm logs include level, request_id, path, status_code, latency.

### Accessibility & Security
1. Run Lighthouse and axe; fix critical issues.
2. Run `npm audit`; note and mitigate vulnerabilities.
3. If metrics endpoint secured, test token requirement.

### UAT
1. Execute user journeys: new query, repeat (cache), invalid query, rate limit scenario.
2. Record outcomes and sign-off.
