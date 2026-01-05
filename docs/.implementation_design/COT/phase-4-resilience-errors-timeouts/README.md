# Phase 4 — Resilience: Errors & Timeouts

## Goal
- Handle failures gracefully and keep long queries connected.

## Scope (KISS)
- Emit a single `error` event if the agent fails mid-stream.
- Send periodic heartbeats to avoid browser timeouts.

## Backend
- Stream error events with concise messages.
- Heartbeat comments every few seconds.

## Frontend
- Show a simple error message and stop streaming on failure.
- Keep the connection alive naturally during long queries.
- CoT is presented in the frontend UI; on error, CoT stops and a single concise message is shown.

## Acceptance Criteria
- Users see a clear error message when things go wrong.
- Long-running queries do not disconnect abruptly.

## Risks & Mitigations
- Overly technical errors: simplify to user language.
