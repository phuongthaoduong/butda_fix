# Phase 4 – Quality, Observability & Release Readiness

## Overview

Finalize the MVP by hardening quality, observability, and operational workflows so that the application can be shared with stakeholders. This phase emphasizes test coverage, monitoring hooks, documentation, and manual release procedures for the local-first deployment strategy.

## Objectives
- Achieve agreed-upon automated test coverage across backend and frontend.
- Establish logging, metrics, and alerting hooks suitable for a small-scale launch.
- Document manual release checklist and rollback plan.
- Capture known limitations and next-step roadmap beyond the MVP.
- Conduct final accessibility, security, and performance validations.

## User-Facing Test
Stakeholders can run through scripted user journeys (happy path, error path, cache hit) with confidence that failures are captured, metrics are collected, and documentation exists for support and maintenance.

## Scope & Deliverables

### Backend
- Test coverage:
  - Unit tests for services, validators, caching, error handling.
  - Integration tests for `/api/research`, `/api/health`, rate limiting, metrics.
  - Use `pytest-cov`; enforce thresholds (e.g., 85%).
- Observability:
  - Finalize metrics endpoint using `prometheus_client`.
  - Confirm structured logging outputs consumed by log aggregator (even if local).
  - Provide configuration validation at startup:
    - Ensure required env vars present; exit with informative error if missing.
- Feature toggles:
  - Introduce config flags: `ENABLE_CACHE`, `ENABLE_RATE_LIMITING`, `ENABLE_METRICS`.
  - Document defaults in `.env.example`.
- Security hardening:
  - Add simple authentication guard for metrics endpoint (optional token).
  - Run security linters (Bandit) and address findings.

### Frontend
- Testing:
  - Expand unit coverage (components, hooks).
  - Integration tests with mocked network using MSW.
  - E2E tests via Cypress/Playwright hitting real backend (in dev mode).
- Accessibility:
  - Run automated audit (Lighthouse/axe) and fix issues (contrast, semantics, focus).
  - Add keyboard navigation tests for modals/filters.
- Build configuration:
  - Introduce separate `.env.production`.
  - Add `npm run build:release` that outputs artifacts ready for hosting.
- Analytics & Telemetry:
  - Stub handler to log query submissions/events (console or mock service).
  - Provide extension point for future real analytics integration.

### Integration & Operations
- Manual release checklist:
  - Pre-release: ensure tests pass, update docs, bump version.
  - Build steps: backend package, frontend dist bundle.
  - Deployment: copy artifacts to target, configure environment, run smoke tests.
  - Rollback: documented steps to revert to previous build.
- Incident response playbook:
  - Outline detection, communication, mitigation steps.
  - Provide contact list / escalation path (placeholder for now).
- Troubleshooting FAQ:
  - Common issues: agent latency, cache mismatch, rate limiting, env misconfig.
- Roadmap document summarizing future improvements (post-MVP).
- UAT scripts for stakeholders; record results and sign-off.

## Technical Implementation Outline
1. **Testing Expansion**
   - Backend: add tests in `server/tests/unit` and `server/tests/integration`.
   - Frontend: add suites under `client/src/__tests__` and `client/cypress`.
   - Update GitHub Actions to run coverage reports and fail below thresholds.
2. **Observability Plumbing**
   - Implement `prometheus_client` integration.
   - Ensure logs include log level, request ID, component, message.
   - Update docs on how to scrape metrics locally (Prometheus optional, instructions for curl).
3. **Configuration Validation**
   - Add startup script verifying env vars; raise `RuntimeError` if invalid.
   - Provide helpful error messages with resolution steps.
4. **Release Documentation**
   - Create `docs/release/README.md` with step-by-step manual release & rollback.
   - Include checklists, template release notes, artifact naming conventions.
5. **QA & UAT**
   - Compile user journey scripts covering:
     - New query, repeat query (cache), invalid query, rate limited scenario.
   - Capture results in `docs/testing/uat-report.md`.
6. **Accessibility & Security Audit**
   - Run Lighthouse/Axe; document issues + resolutions.
   - Run Bandit, npm audit; fix or document any remaining vulnerabilities.
7. **Handoff & Roadmap**
   - Schedule final review meeting.
   - Produce roadmap doc outlining features deferred beyond MVP.

## Dependencies & Assumptions
- Core functionality from Phases 1-3 is feature-complete and stable.
- Team agrees on minimum coverage thresholds (e.g., backend 80%, frontend 70%).
- Access to necessary testing tools (Cypress, Locust) in local environment.

## Acceptance Criteria
- CI pipeline passes:
  - Backend unit + integration tests with coverage >= agreed threshold.
  - Frontend unit + e2e tests with coverage >= agreed threshold.
  - Linting/security checks (ruff, eslint, bandit, npm audit) clean or noted.
- Manual release dry run completed, with artifacts produced and smoke-tested.
- Observability verified:
  - Metrics endpoint accessible (with optional token), logs structured.
  - Alert simulation (e.g., threshold breach) documented or performed.
- UAT scripts executed by stakeholder representative; feedback recorded with no blocking issues.
- Documentation:
  - Release manual, rollback plan, troubleshooting FAQ, roadmap all published.
  - Known limitations and future enhancements captured.
- Accessibility audit passes (no critical issues) and security scans addressed.

## Metrics & Diagnostics
- Capture and archive:
  - Coverage reports (HTML artifacts).
  - Test run durations (unit, integration, e2e).
  - Performance metrics from Phase 3 re-run.
- Provide list of key metrics/logs for monitoring post-release (requests, latency, cache hits, rate limits).
- Maintain risk register or issue tracker for remaining technical debt.
- Document alert thresholds (e.g., error rate >5%, response time >5s).

## Risks & Mitigations
- **Risk:** Tight timeline limits test depth.  
  **Mitigation:** Prioritize critical paths; document gaps explicitly.
- **Risk:** Observability adds runtime overhead.  
  **Mitigation:** Keep instrumentation lightweight and configurable via env flags.
- **Risk:** Manual release process error-prone.  
  **Mitigation:** Invest in detailed checklists and templates; pair on first run.

## Exit Checklist
- [ ] Automated tests (backend + frontend) implemented, passing, and meeting coverage targets.
- [ ] CI pipeline includes linting, security scans, and test suites.
- [ ] Manual release checklist, rollback plan, and artifact storage instructions published.
- [ ] Observability plumbing verified (metrics endpoint, structured logs, alert plan).
- [ ] Accessibility and security audits completed; issues resolved/documented.
- [ ] Final documentation pack delivered (runbooks, FAQ, troubleshooting, roadmap, UAT report).
- [ ] Stakeholder sign-off recorded; production-readiness status noted.

