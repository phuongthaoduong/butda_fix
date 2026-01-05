# Phase 1 — Streaming Backbone

## Goal
- Stream simple progress updates and a final result, so users can see that BUTDA is actively working.

## Scope (KISS)
- Minimal progress stages: Starting → Loading → Searching → Reading → Thinking → Writing → Complete.
- Heartbeats keep the connection alive on long queries.
- No extra configuration required for users.

## Backend
- Add `GET /api/research/stream` (SSE) that emits progress events and a final `complete` event.
- Use the existing agent runner with an async bridge to stream events in real time.

## Frontend
- Connect via EventSource and display short status messages while waiting for the answer.
- CoT is presented in the frontend UI during processing and is not persisted.

## Acceptance Criteria
- Users see live progress messages, then the final summary.
- Progress stops and the answer remains.

## Risks & Mitigations
- Long queries dropping: send periodic heartbeat comments.
- Mid-stream errors: emit a single, clear `error` event.
