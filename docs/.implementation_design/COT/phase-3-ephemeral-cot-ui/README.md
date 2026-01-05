# Phase 3 — Ephemeral CoT UI

## Goal
- Show the Chain of Thoughts only while BUTDA is working; remove it when the answer is ready.

## Scope (KISS)
- CoT is temporary and non-persistent.
- Final view focuses solely on the answer.

## Backend
- No changes (stream continues to emit progress and final result).

## Frontend
- Automatically clear CoT when `event: complete` arrives.
- Keep the final answer visible and readable.
- CoT is presented in the frontend UI only during processing; it disappears automatically on completion.

## Acceptance Criteria
- Users never have to manually hide CoT.
- The final screen is uncluttered and focused on the result.

## Risks & Mitigations
- CoT lingering due to race conditions: ensure completion handler clears state once.
