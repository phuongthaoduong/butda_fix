# Phase 2 — Frontend Stream Connection

## Goal
- The UI connects to the stream and shows progress in a friendly, readable way.

## Scope (KISS)
- Display only the current stage and a short message.
- Keep layout simple and focused; no technical terms.

## Backend
- No changes (reuse Phase 1 stream endpoint).

## Frontend
- Use a dedicated hook to manage the EventSource connection and state.
- Render a compact progress area while BUTDA is working.
- CoT is presented in the frontend UI and disappears when the final result arrives.

## Acceptance Criteria
- Users see live, readable progress in the UI.
- No duplicated or noisy messages.

## Risks & Mitigations
- Invalid URLs causing failures: build stream URL robustly (dev/prod).
- Browser timeouts: rely on heartbeat to keep the connection alive.
