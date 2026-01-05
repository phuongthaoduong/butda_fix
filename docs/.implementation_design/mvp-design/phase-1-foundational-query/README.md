# Phase 1 – Foundational Query Flow

## Overview

Establish the minimal end-to-end experience that lets a user submit a research query and receive a visible response. During this phase the backend may return mocked data, but the UI and API contract must reflect the final shape so that subsequent phases can focus on richer functionality.

## Objectives
- Stand up the FastAPI backend skeleton with `/api/research` and `/api/health` endpoints wired through the service layer.
- Deliver a React/Vite frontend with a working query form and basic result display placeholders.
- Ensure the frontend talks to the backend via environment-driven base URLs.
- Produce developer documentation for local startup and smoke testing.
- Establish foundational tooling (linting, formatters, task scripts) so future phases only iterate on functionality.

## User-Facing Test
From a browser, a user can visit the frontend, enter a query, submit it, and see a stubbed summary plus empty result cards confirming the request succeeded.

## Scope & Deliverables

### Backend
- Implement directory layout per master design doc (`server/app/api`, `app/services`, etc.).
- Create `ResearchRequest`, `ResearchResponse`, and related Pydantic models (`app/models/schemas.py`).
- Implement `/api/research` and `/api/health` routers; research endpoint returns deterministic stub.
- Add service layer (`app/services/research_service.py`) with `process_research*` returning stubbed payload.
- Configure logging (`app/core/logging.py`) with INFO-level console handler.
- Provide example response JSON in `server/tests/snapshots/research_stub.json`.

### Frontend
- Scaffold Vite + React + TypeScript project (per design doc structure).
- Implement base components:
  - `Header` with product title and subtitle.
  - `SearchForm` with validation (≥3 characters, ≤ `VITE_MAX_QUERY_LENGTH`).
  - `LoadingSpinner`, `ErrorMessage`.
  - `ResultDisplay` reading schema fields.
- Set up React context/hook (`useResearch`) that hits backend endpoint.
- Add minimal styling via CSS modules or Tailwind (if configured) to match MVP look.
- Include placeholder empty-state panel when no search executed.

### Integration & Tooling
- Provide `.env.example` files in both `client/` and `server/` with documented keys.
- Add `npm run lint`, `npm run format`, and `uv run ruff`/`black` scripts (if using).
- Update deployment/testing design doc with Phase 1 smoke checklist.
- Create initial tests:
  - Backend: `pytest` for health endpoint and schema validation (use stub data).
  - Frontend: smoke test verifying `SearchForm` renders and submit button disabled <3 chars.

## Technical Implementation Outline
1. **Backend scaffold**
   - Run `uv pip install fastapi uvicorn pydantic python-dotenv`.
   - Create `server/app/main.py` (if not existing) and register routers.
   - Implement `app/api/endpoints/research.py` returning stub via service.
   - Sample stub response:
     ```python
     return {
         "query": query,
         "summary": "Initial summary placeholder for '{query}'",
         "results": [
             {"id": "stub-1", "title": "Placeholder result 1", "url": "https://example.com/1", "snippet": "Lorem ipsum...", "publishedAt": datetime.utcnow(), "source": "Example Source", "relevanceScore": 0.5}
         ],
         "sources": [
             {"name": "Example Source", "url": "https://example.com", "reliability": "medium", "type": "article"}
         ],
         "statistics": {"totalResults": 1, "processingTime": 10, "searchTime": 5, "summaryTime": 5},
         "cached": False,
     }
     ```
2. **Frontend scaffold**
   - `npm create vite@latest client -- --template react-ts`.
   - Install dependencies (axios, tailwind optional).
   - Implement `src/services/api.ts` using `VITE_API_URL`.
   - Implement `useResearch` calling `/api/research`.
3. **Connect frontend ↔ backend**
   - Ensure CORS configured using `CORS_ORIGINS`.
   - Validate `.env` values in both projects.
4. **Testing hooks**
   - Add `pytest` test: `TestClient(app).post("/api/research", json={"query": "test"})`.
   - Add frontend test: `SearchForm` enabling submit on valid input, `useResearch` mock verifying API call.
5. **Documentation**
   - Update `docs/.implementation_design/design/DEPLOYMENT_TESTING_IMPLEMENTATION.md` manual steps.
   - Provide `docs/.implementation_design/mvp-design/phase-1-foundational-query/testing.md` (optional) listing manual steps.

## Dependencies & Assumptions
- Python 3.9+ and Node 18+ available locally.
- No Redis requirement; cache disabled via empty `REDIS_URL`.
- AgentHub integration deferred to Phase 2.
- Tailwind utilities optional; vanilla CSS acceptable initially.

## Acceptance Criteria
- POST `/api/research` returns 200 with body adhering to schema (validated via `pydantic`).
  - Response contains `summary` string, `results` list (≥1 entry), `sources` list, `statistics` object, and `cached` boolean.
- GET `/api/health` returns 200 with `status: "healthy"`.
- Frontend allows user to submit query and renders stub summary/results within 1 second.
- Loading spinner present while awaiting response; form disabled during request.
- Validation errors:
  - Query <3 chars → inline message + disabled button.
  - Query exceeds max length → error toast/message.
- Developer documentation includes: setup steps, commands to start both services, curl smoke tests, manual UI test script.
- Basic automated tests (backend + frontend) passing locally.

## Metrics & Diagnostics
- Console logs show each request with timestamp, query length, and response latency.
- Provide manual checklist for verifying:
  - Network request in browser devtools.
  - Response payload shape.
  - Frontend state transitions (loading, success, error).
- Record response time of stubbed endpoint (<200 ms locally) and note in README for baseline.
- Add TODO for integrating structured logging in later phases.

## Risks & Mitigations
- **Risk:** Schema drift between backend and frontend.  
  **Mitigation:** Reuse shared types/spec from design docs; add JSON schema sample in README if needed.
- **Risk:** Developers blocked by environment configuration.  
  **Mitigation:** Commit `.env.example` files with required keys and defaults.

## Exit Checklist
- [ ] Backend stub returns structured response for any valid query (including whitespace normalization).
- [ ] Frontend form submits to backend and renders data (summary, single stub result, source).
- [ ] Loading/error states behave as expected.
- [ ] Unit/integration smoke tests implemented and passing.
- [ ] `.env.example` files created with documented defaults.
- [ ] Updated docs describing how to run and test locally (including curl command and browser checklist).
- [ ] Known gaps and next-phase dependencies captured in project tracker / README “Next Steps” section.

