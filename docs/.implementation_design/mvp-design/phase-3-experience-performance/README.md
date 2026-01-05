# Phase 3 – Experience, Performance & Guidance

## Overview

Elevate the user experience with richer presentation, responsiveness, and supporting guidance while hardening performance characteristics. This phase focuses on helping users interpret results quickly and providing responsive feedback during longer-running research tasks.

## Objectives
- Improve frontend presentation with formatting, pagination/sectioning, and contextual tips.
- Introduce client-side retries and optimistic UI signals for long queries.
- Enhance backend with rate limiting, request validation, and structured logging.
- Provide user guidance such as tips, empty-state messaging, and FAQ/help content.
- Benchmark and optimize performance for typical and heavy query loads.

## User-Facing Test
When submitting complex or repeated queries, the user experiences responsive feedback (e.g., progress messaging), clearly formatted summaries, sortable results, and helpful guidance explaining how to interpret outcomes or refine queries.

## Scope & Deliverables

### Backend
- Implement rate limiting middleware:
  - Use Redis-backed sliding window or token bucket (e.g., `asyncio` + Redis counter).
  - Configurable via `RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`.
  - Include per-IP key using `request.client.host`.
- Strengthen validation:
  - Sanitize query input (strip whitespace, reduce repeated spaces).
- Introduce structured logging:
  - Configure `app/core/logging.py` for JSON output including `request_id`, `status`, `latency`.
  - Add middleware to inject `X-Request-ID` header (use `uuid4`).
- Optional metrics endpoint:
  - `/api/metrics` exposing Prometheus counters (requests total, latency histogram, cache hits).
- Performance tuning:
  - Use async HTTP client for agent if supported.
  - Introduce configurable timeouts and retries for agent calls.

### Frontend
- Upgrade UI components:
  - `ResultDisplay` organizes data into tabs or sections (Summary, Articles, Sources, Insights).
  - Provide sort dropdown (e.g., Relevance, Newest).
  - Add filter toggles (e.g., source type, reliability tiers).
- Loading/feedback:
  - Add skeleton placeholders for summary and results.
  - Provide progress messaging (e.g., "Research in progress…").
  - Implement retry button with countdown for rate-limited responses.
- Guidance:
  - Add helper component with tips (e.g., "Try narrowing your query…").
  - Provide FAQ modal or side panel with 3–5 curated Q&A entries.
- Accessibility:
  - Ensure components have aria labels, focus trapping for dialogs, keyboard navigation.

### Integration & Tooling
- Frontend captures and displays `X-Request-ID` from responses (visible to support).
- Update Axios interceptor to attach request ID to logs.
- Document performance testing approach (Locust/Artillery script).
- Add feature flags (e.g., query filtering) controlled via env or config file.
- Provide documentation for troubleshooting rate limit hits and latency.

## Technical Implementation Outline
1. **Rate Limiting Middleware**
   - Create `app/api/dependencies/rate_limit.py`.
   - On each request, increment Redis key `rl:{ip}:{current_window}`; deny if count > limit.
   - Return HTTP 429 with JSON body `{ "error": { "code": "RATE_LIMITED", ... } }`.
2. **Structured Logging**
   - Configure logging using `structlog` or standard `logging` with JSON formatter.
   - Middleware attaches `request_id` to context; responses include header.
3. **Frontend Enhancements**
   - Extend `ResultDisplay` to accept new props: `sortBy`, `filters`.
   - Implement state management (React context or `useReducer`) for filters.
   - Add components: `ResultFilterBar`, `InsightsPanel`, `TipsPanel`.
4. **Guidance Content**
   - Create `src/content/faq.ts` containing Q&A entries.
   - Display modal accessible via "Need help?" link.
5. **Performance Profiling**
   - Write Locust file hitting `/api/research` with varying query sizes.
   - Document results (baseline vs. optimized).
6. **Testing**
   - Backend: tests for rate limiting (within limit vs. exceeding), structured logs (via caplog), sanitized queries.
   - Frontend: tests for filter interactions, skeleton display during loading, FAQ modal accessibility.
7. **Documentation**
   - Add `performance.md` with profiling steps/results.
   - Update deployment doc with rate limit troubleshooting.

## Dependencies & Assumptions
- Phase 2 functionality is stable with live agent responses.
- Redis available for rate limiting counters (or fallback in-memory for development).
- Team alignment on UX enhancements (wireframes or mockups available if needed).

## Acceptance Criteria
- Rate limiting enforced per configuration; user sees friendly message with retry countdown on 429.
- Structured logs produced for each request with fields: `request_id`, `path`, `status_code`, `latency_ms`, `cache_status`.
- Frontend provides:
  - Organized results (tabs/sections).
  - Sorting/filtering controls that update display.
  - Loading skeletons and tips/FAQ accessible.
- Performance benchmarks documented:
  - P95 response time target (e.g., ≤5s for typical queries) met under simulated load.
- Accessibility checks: keyboard navigation for filters, ARIA attributes on modals.
- Updated documentation: UX testing checklist, rate limit guide, performance summary.

## Metrics & Diagnostics
- Backend metrics:
  - `requests_total` (labels: status, cache_status).
  - `request_duration_seconds` histogram.
  - `rate_limited_total`.
- Frontend telemetry (console logs or stub analytics):
  - Record time from submit to response.
  - Capture filter usage counts.
- Provide template for future dashboard (e.g., Grafana panels).
- Gather qualitative feedback: note confusion points, improvement ideas.

## Risks & Mitigations
- **Risk:** UX changes complicate baseline layout.  
  **Mitigation:** Implement incrementally with feature flags or toggles.
- **Risk:** Rate limiting blocks genuine users.  
  **Mitigation:** Tune thresholds; add developer override via environment variables.
- **Risk:** Additional UI complexity introduces regressions.  
  **Mitigation:** Add frontend tests (unit + integration) covering new interactions.

## Exit Checklist
- [ ] Rate limiting enforced and tested (happy path + throttled).
- [ ] Structured logging emitting JSON with request IDs; headers returned to client.
- [ ] Frontend UX enhancements implemented (sorting/filtering, skeletons, guidance).
- [ ] Accessibility audit completed with fixes applied.
- [ ] Performance profiling executed; results documented with bottlenecks addressed.
- [ ] Updated help/FAQ content and troubleshooting guides committed.
- [ ] Metrics/diagnostics plan documented for future monitoring integration.

