# Phase 4 — User Testing

## How to Test
- Temporarily break the agent (e.g., stop the tool server) and submit a query.
- Submit a long query and watch for continued connection (heartbeat).

## What to Look For
- A single, plain error message when the agent fails.
- No technical jargon in the UI.
- Heartbeats appear (visible in Network/SSE events); stream continues.

## Pass/Fail
- Pass: Clear error + robust long-query behavior.
- Fail: Silent failures or dropped connections.

