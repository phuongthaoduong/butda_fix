# Phase 2 – Agent Integration & Real Results

## Overview

Replace the mocked research flow with live data from the AgentHub research agent and ensure the UI surfaces meaningful summaries, results, and sources. This phase validates the core value proposition by letting users run real research queries end-to-end.

## Objectives
- Wire `AgentService` to load and invoke the AgentHub `research-agent` with configurable parameters.
- Implement Redis-backed caching and graceful degradation if Redis is unavailable.
- Enhance frontend result cards to render real data (titles, snippets, links, sources).
- Capture errors across the stack and present actionable messaging to users.
- Introduce observability hooks (timers, logging) to monitor live agent performance.

## User-Facing Test
From the frontend, a user enters a real-world research question and receives an AI-generated summary with supporting articles pulled from the agent. Re-running the same query returns instantly (cache hit indicator visible).

## Scope & Deliverables

### Backend
- Implement live agent integration:
  - Update `AgentService` to call `ah.load_agent("agentplug/research-agent", external_tools=["web_search"])`.
  - Map agent results into schema, handling missing fields.
  - Provide async and sync variants (`standard_research` may be blocking; wrap as needed).
- Implement Redis cache wrapper:
  - `redis.from_url(REDIS_URL, decode_responses=True)`.
  - Cache key: `research:{hash(query.lower())}` for stability.
  - TTL configurable via `CACHE_TTL_SECONDS`.
  - Graceful fallback when Redis unavailable (log warning, disable cache).
- Add metrics/tracing:
  - Collect `search_time`, `processing_time`, `summary_time` from agent metadata or measured durations.
  - Log agent invocation start/end with duration.
- Expand error handling:
  - Distinguish user errors (validation, query too long) vs. system errors (agent failure, network).
  - Return structured `error` object with `code`, `message`, `details`.

### Frontend
- Update `ResultDisplay` to render:
  - Summary text with basic formatting (paragraphs).
  - Results list containing title, snippet, formatted timestamp, `View Source` link.
  - Source cards with reliability badges and type chips.
  - Statistics component showing total results, search time, processing time, cache flag.
- Implement error handling UI:
  - Catch API errors and display friendly message with optional retry CTA.
  - Differentiate between validation errors (from backend) and connectivity issues.
- Add caching indicator (badge + tooltip) when `data.cached` true.
- Ensure all external links open in new tabs with `rel="noopener noreferrer"`.
- Add unit/integration tests covering rendering of dynamic data and errors.

### Integration & Tooling
- Update `.env.example` with AgentHub configuration (if required):
  - `AGENTHUB_API_KEY`, `AGENTHUB_ENV`, etc.
  - Document how to obtain credentials (link to internal wiki or AgentHub docs).
- Document Redis setup:
  - Local installation instructions (e.g., `brew install redis`).
  - Commands to start/stop, verify connection (`redis-cli ping`).
- Extend testing doc with manual scenarios:
  - First query vs. repeated query (cache hit).
  - Query when Redis offline.
  - Query when AgentHub unreachable.


## Technical Implementation Outline
1. **Dependencies**
   - Backend: `uv pip install redis httpx agenthub`.
   - Frontend: ensure `date-fns` (or similar) for timestamp formatting.
2. **Agent Integration**
   - Update `AgentService.__init__` to load agent once (reuse per request).
   - Implement `_process_agent_result` handling:
     - `result.get("summary")`, `result.get("results")`, `result.get("sources")`.
     - Normalize missing fields; convert timestamps to ISO strings.
   - Add timeout handling (`SEARCH_TIMEOUT` env).
3. **Caching Layer**
   - Introduce helper class `CacheClient` (optional) for get/set operations.
   - Wrap agent call with cache check:
     ```python
     cache_key = f"research:{hashlib.sha256(query.lower().encode()).hexdigest()}"
     if cached := self.redis_client.get(cache_key):
         ...
     ```
   - When storing result, include `cached=False`; on retrieval set `cached=True`.
4. **Error Handling**
   - Use custom exceptions for agent failures; map to HTTP status codes.
   - Log errors with stack trace for debugging (but avoid exposing sensitive info to clients).
5. **Frontend Enhancements**
   - Extend TypeScript interfaces to align with real data (dates as ISO strings).
   - Format `publishedAt` using `new Date(...).toLocaleDateString()` or `date-fns`.
   - Add `useEffect` to scroll to results upon successful fetch.
   - Provide message when `results` empty but summary present.
6. **Testing**
   - Backend integration tests hitting `/api/research` and verifying response structure when agent mocked.
   - Add tests covering cache behavior (mock Redis).
   - Frontend: integration test mocking API response with real-like payload; error state test.
7. **Documentation**
   - Update Phase 2 README with sample responses.
   - Record manual QA steps and expected outcomes in `testing.md`.
   - Document how to seed cache manually if needed.

## Dependencies & Assumptions
- Phase 1 deliverables complete and stable.
- AgentHub access tokens or API keys configured locally.
- Redis installed locally (Homebrew or equivalent) or accessible via Docker container if desired.
- Network connectivity for AgentHub and downstream web search tools.

## Acceptance Criteria
- Live agent responses returned within configured timeout; user-visible summary and ≥1 result displayed for typical queries.
- Repeated query within TTL returns cached data (UI badge + quicker response).
- Redis outages do not break API (requests succeed without caching; warning logged).
- Frontend differentiates between success (`success: true`) and error responses; user sees useful messaging and optional retry.
- Backend logs include agent duration, cache hit/miss, and error codes.
- Manual test cases documented and executed:
  - Happy path query.
  - Repeat query (cache hit).
  - Redis offline scenario.
  - AgentHub failure simulated (mock raising exception).
- Automated tests updated to cover caching and agent integration (with mocks).

## Metrics & Diagnostics
- Instrument timing for:
  - `agent_call_duration_ms`
  - `cache_lookup_duration_ms`
  - `total_processing_time_ms`
- Count metrics (even if just logged for now):
  - `cache_hits`, `cache_misses`, `agent_errors`, `user_errors`.
- Provide manual metrics checklist:
  - Compare response time fresh vs. cached (<50% of original).
  - Confirm logs show appropriate counts for tests run.
- Store example responses with sanitized content in `docs/examples/phase-2/`.

## Risks & Mitigations
- **Risk:** AgentHub latency impacts UX.  
  **Mitigation:** Add timeout configuration, show loading states, consider partial results.
- **Risk:** Redis outages break flow.  
  **Mitigation:** Wrap cache access in try/except; proceed without caching if unavailable.
- **Risk:** Data variability complicates UI assumptions.  
  **Mitigation:** Validate fields before rendering; provide defaults/fallbacks.

## Exit Checklist
- [ ] AgentHub integration operational; real data visible in UI for representative queries.
- [ ] Redis caching functioning with documented setup + fallback path.
- [ ] UI renders live summaries, results, sources, stats including cache indicator.
- [ ] Error handling (agent failure, Redis down, validation errors) tested and documented.
- [ ] Logging includes agent timings and cache metrics.
- [ ] Example responses and manual QA results stored under `docs/examples/phase-2`.
- [ ] Documentation updated for environment variables, testing steps, troubleshooting tips.

