# Repository Guidelines

## Project Structure & Module Organization
The repository is split into three live services plus helper assets. `client/` hosts the Vite + React UI with feature code under `src/components`, hooks in `src/hooks`, axios wrappers in `src/services`, and colocated unit tests in `src/__tests__`. `server/` runs the FastAPI backend: routers in `app/api`, shared settings and caching helpers in `app/core`, domain models in `app/models`, and async workers in `app/services`; API tests live in `server/tests`. `research-agent/` contains the MCP tool server (`tool_server.py`) and the AgentHub driver used for integration tests. Shared operational scripts sit in `scripts/`, while product docs and assets belong in `docs/`.

## Build, Test, and Development Commands
- `./scripts/install.sh` — create the Python virtualenv, install FastAPI dependencies, and run `npm install` for the frontend (run after cloning or when dependencies change).
- `./scripts/start-toolserver.sh`, `./scripts/start-backend.sh`, `./scripts/start-frontend.sh` — launch the three services on ports 8000/8001/5173; keep each terminal open during development.
- Frontend: `npm run dev` for hot reload, `npm run build` to emit `client/dist`, `npm run lint` for ESLint, and `npm run test` or `npm run test:watch` for Vitest suites.
- Backend: `source server/.venv/bin/activate && uvicorn main:app --reload` mirrors the start script; run `python -m pytest server/tests` for API tests and `python server/test_multiple_queries.py` for AgentHub smoke coverage.

## Coding Style & Naming Conventions
TypeScript files use two-space indentation, top-level functional React components, and PascalCase filenames for components (`ResultDisplay.tsx`). Hooks and utility files stay camelCase and belong in `hooks/` or `utils/`. Keep types in `client/src/types` and prefer explicit return types for exported functions. ESLint (run via `npm run lint`) enforces import ordering and React Hook rules—fix warnings before pushing. Python code follows PEP 8 with type hints; keep business logic inside `app/services` and expose thin routers under `app/api`. Module names, functions, and variables stay snake_case, and shared schemas belong to `app/models`.

## Testing Guidelines
Frontend unit tests should mirror the directory under test (e.g., `components/__tests__/Header.test.tsx`) and rely on Vitest plus Testing Library assertions; write at least one state/regression test per UI change. Backend additions need pytest coverage that hits both success and failure paths and can run with `pytest -q server/tests`. When touching agent orchestration, update or extend `server/test_multiple_queries.py` to demonstrate the new behavior. Aim to keep tests deterministic by mocking HTTP requests (axios interceptors client-side, httpx mocks server-side).

## Commit & Pull Request Guidelines
Follow the conventional commit style already in the log (`feat(client): …`, `chore: …`, `fix(server): …`). Scope the prefix to the folder you touched and keep the subject under ~70 characters; add focused body bullets when the change spans multiple services. Each PR should include: a one-paragraph summary, a checklist of services impacted (client/server/tool server), linked issues (`Closes #123`), environment or config changes (mention `.env` keys), and before/after screenshots for UI tweaks. Request reviews only after CI/test commands above pass locally.

## Security & Configuration Tips
Never commit `.env` files. `server/.env` must include `OPENAI_API_KEY`, and `client/.env` (copied from `.env.example`) should only contain non-secret URLs. If you rotate API keys, re-run `./scripts/clean.sh --full` before `./scripts/install.sh` to refresh the virtualenv. Keep the tool server accessible only on localhost; if you expose ports externally, wrap uvicorn/vite with HTTPS or a tunnel so API keys remain safe.
