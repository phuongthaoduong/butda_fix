# Repository Guidelines

## Project Structure & Module Organization
The monorepo hosts three live services. `client/` is a Vite + React UI with feature components under `src/components`, hooks in `src/hooks`, axios wrappers in `src/services`, and colocated unit tests in `src/__tests__`. `server/` contains the FastAPI backend: routers live under `app/api`, shared config and caching helpers under `app/core`, models in `app/models`, and async workers in `app/services`; pytest suites are in `server/tests`. `research-agent/` exposes the MCP tool server (`tool_server.py`) that the backend calls during research flows. Shared scripts sit in `scripts/`, while assets and docs live in `docs/`.

## Build, Test, and Development Commands
Run `./scripts/install.sh` after cloning to bootstrap the Python virtualenv, agent dependencies, and `npm install`. Use the trio of start scripts (`start-toolserver.sh`, `start-backend.sh`, `start-frontend.sh`) to launch services on ports 8000/8001/5173, or run `npm run dev` plus `uvicorn main:app --reload` manually. Frontend checks: `npm run build`, `npm run lint`, and `npm run test` (or `test:watch`). Backend checks: `python -m pytest server/tests` and `python server/test_multiple_queries.py` for AgentHub coverage. `./scripts/clean.sh --full` wipes caches before re-installing if dependencies drift.

## Coding Style & Naming Conventions
React code uses two-space indentation, PascalCase component files (e.g., `ResultDisplay.tsx`), and camelCase hooks/utilities in their respective folders. Place shared types in `client/src/types` and prefer explicit return types on exports. ESLint (`npm run lint`) enforces import order and React Hook rules; fix warnings before commits. Python follows PEP 8 with type hints, snake_case names, and business logic isolated in `app/services` while routers stay thin wrappers in `app/api`.

## Testing Guidelines
Frontend tests live next to the code under `src/__tests__` and use Vitest with Testing Library; mirror the component tree when naming files (e.g., `components/__tests__/Header.test.tsx`). Backend code requires pytest coverage that exercises both success and failure paths, and HTTP calls should be mocked via httpx fixtures. When modifying agent orchestration, extend `server/test_multiple_queries.py` to prove regressions are covered.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits scoped by folder (`feat(client):`, `fix(server):`). Keep subjects under ~70 characters and add bullet bodies when touching multiple services. Pull requests must summarize the change in one paragraph, check off affected services (client/server/tool server), link issues (`Closes #123`), list env/config deltas, and attach before/after UI screenshots when relevant. Ensure all commands above pass locally before requesting review.

## Security & Configuration Tips
Never commit `.env` files. Copy `server/.env.example` and add `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` plus any tool host variables, while `client/.env` should only contain non-secret URLs such as `VITE_API_URL`. Keep the tool server private to localhost or an internal network; if you expose ports externally, protect them with HTTPS or tunneling so API keys remain safe.
