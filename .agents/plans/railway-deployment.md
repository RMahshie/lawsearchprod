# Railway Deployment

## Goal
Deploy LawSearch to Railway with a working production frontend, FastAPI backend, Postgres metadata database, and persistent Chroma vector store. The deployed app must support normal query flow, saved history, citation hover rehydration, and vector-store ingestion/activation without relying on local development paths.

## Non-Goals
Do not change RAG prompt behavior, model strategy, retrieval semantics, ingestion parsing, saved-history storage format, or frontend citation rendering.

Do not switch the primary deployment target away from Railway in this plan.

Do not preserve any deployment path that silently falls back to a wrong Chroma root, missing vector store, local-only API URL, or invented `chunk_id`.

Do not optimize OpenAI cost by changing model choices unless the user explicitly approves that as a separate change.

## Current Behavior
The repo is containerized for local Docker Compose with three services: `backend`, `frontend`, and `postgres`.

`Dockerfile.backend` runs FastAPI with `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Railway commonly injects the public service port through `PORT`, so the current backend image is likely to need a production start-command or Dockerfile adjustment to bind to Railway's assigned port.

`docker-compose.yml` sets backend runtime values for local containers:
- `OPENAI_API_KEY=${OPENAI_API_KEY}`
- `ENVIRONMENT=production`
- `API_HOST=0.0.0.0`
- `API_PORT=8000`
- `LOG_LEVEL=INFO`
- `VECTORSTORE_DIR=/app/db/chroma`
- `DATA_DIR=/app/data/bills`
- `DATABASE_URL=postgresql+psycopg://lawsearch:lawsearch@postgres:5432/lawsearch`

`Dockerfile.backend` copies `app/`, root `*.py` files, and `data/bills/` into the image, then creates `/app/db/chroma`. `.dockerignore` excludes `db/chroma/`, so the local vector store is not baked into the image and must be supplied through Railway persistent storage or regenerated in Railway.

`Dockerfile.frontend` builds the Vite frontend and serves it with Nginx. Its embedded Nginx config proxies `/api/` to `http://backend:8000/api/`, which works in Docker Compose service networking but may not match Railway service networking.

`frontend/src/services/api.ts` uses `VITE_API_BASE_URL` at build time, falling back to `http://localhost:8000`. For a Railway frontend build, `VITE_API_BASE_URL` must be set before build, or the production frontend will call localhost.

`app/core/config.py` defaults CORS origins to localhost and Docker/Vite development origins. The deployed frontend Railway domain must be allowed by backend CORS if the frontend calls the backend domain directly.

`app/main.py` calls `ensure_storage_ready()` on startup. If `DATABASE_URL` is present, metadata tables and the legacy active vector-store registry row are initialized.

Local size observed before planning:
- `data/`: about `5.8M`
- `db/chroma/`: about `399M`
- repo total: about `711M`

## Proposed Behavior
Railway will run a single project with these services:
- `lawsearch-backend`: FastAPI service built from `Dockerfile.backend`.
- `lawsearch-frontend`: static frontend service built from `Dockerfile.frontend`, unless a later approved change chooses Railway static hosting or another static host.
- `lawsearch-postgres`: Railway Postgres service used by `DATABASE_URL`.
- `lawsearch-chroma-volume`: Railway volume mounted into the backend at `/app/db/chroma`.

The backend will bind to Railway's runtime port. The implementation must use exactly one of these explicit approaches:
- Preferred: update the backend container start command to run `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` using a shell-form command or Railway start command.
- Acceptable alternative: update `app/core/config.py` or `app/main.py` to read `PORT` into `api_port`, then run the app through `python3`/module entrypoint. If this path is chosen, document why it is better than the start-command change.

The frontend will call the deployed backend directly using `public-backend`: set `VITE_API_BASE_URL=https://<backend-railway-domain>` in the Railway frontend service before build and keep direct API calls from the browser.

The backend CORS configuration will include the deployed frontend origin if the frontend calls the backend public domain directly.

The backend will use `DATABASE_URL` supplied by Railway Postgres. No SQLite or local metadata database will be used in production.

The backend will use `VECTORSTORE_DIR=/app/db/chroma`, backed by the Railway volume. The active vector store will be present before production smoke testing. It will be populated by running the app's ingestion flow in Railway to rebuild a fresh vector store from baked-in `data/bills/`, then activating that store through the storage API/UI.

The deployment will fail loudly if the backend cannot find the active vector store or if saved-history source rehydration cannot use persisted `chunk_id`s.

## Relevant Files
`.agents/PLANS.md`

`.agents/plans/railway-deployment.md`

`Dockerfile.backend`

`Dockerfile.frontend`

`docker-compose.yml`

`.dockerignore`

`app/main.py`

`app/core/config.py`

`app/db/session.py`

`app/services/storage_registry.py`

`app/services/rag_service.py`

`app/services/vector_store_service.py`

`frontend/src/services/api.ts`

`frontend/package.json`

`package.json`

`README.md`

`docs/SETUP.md`

`docs/DOCKER_GUIDE.md`

## Assumptions
The user wants the primary deployment on Railway, not Render, Fly.io, Vercel, or a VPS.

The initial deployment should keep the current architecture: separate backend, frontend, Postgres, and filesystem-backed Chroma.

The first production deployment will rebuild Chroma on Railway from source bills rather than uploading the existing local `db/chroma` directory.

Railway will provide a Postgres connection string compatible with SQLAlchemy's `postgresql+psycopg` driver, or the app will normalize the Railway URL explicitly instead of relying on driver inference.

The production backend should run with `ENVIRONMENT=production`, `LOG_LEVEL=INFO`, and `DEBUG=false` unless the user explicitly wants debug logs enabled temporarily for smoke testing.

No secrets should be committed. Railway variables must hold secret values.

## Open Questions
Answered deployment inputs:

1. Railway project name: `lawsearch`.
2. Backend Railway service name: `lawsearch-backend`.
3. Frontend Railway service name: `lawsearch-frontend`.
4. Postgres Railway service name: `lawsearch-postgres`.
5. Backend domain: Railway-generated domain assigned during deployment.
6. Frontend domain: Railway-generated domain assigned during deployment.
7. Chroma population method: `reingest-on-railway`.
9. Custom domain: do not configure a custom domain for the first deployment; use Railway-generated domains.
10. Deploy method: GitHub auto-deploys.

8. Backend exposure strategy: `public-backend`.

No open deployment questions remain before implementation.

## Execution Steps
- [x] Confirm the remaining backend exposure strategy before implementation starts: `public-backend`.
- [x] Inspect Railway docs for current service, variable, private-networking, volume, and deploy-command behavior before editing code.
- [x] Decide and record the backend port strategy: Dockerfile shell `CMD` using `${PORT:-8000}`.
- [x] Decide and record the frontend API strategy from the backend exposure choice: direct backend public URL through `VITE_API_BASE_URL`.
- [x] Update backend deployment configuration so FastAPI binds to Railway's runtime port while preserving local Docker Compose behavior.
- [x] Update frontend deployment configuration so production builds never fall back to `http://localhost:8000`.
- [x] Update CORS configuration so the exact Railway frontend origin is allowed when using direct browser-to-backend API calls.
- [x] Add Railway deployment documentation with exact required services, env vars, volume mount path, build/start settings, and first-deploy ordering.
- [ ] Create the Railway project and add the Postgres service.
- [ ] Create the backend service from the repo using `Dockerfile.backend`.
- [ ] Attach a persistent Railway volume to the backend at `/app/db/chroma`.
- [ ] Set backend variables exactly:
  - `OPENAI_API_KEY=<secret>`
  - `ENVIRONMENT=production`
  - `DEBUG=false`
  - `LOG_LEVEL=INFO`
  - `DATA_DIR=/app/data/bills`
  - `VECTORSTORE_DIR=/app/db/chroma`
  - `DATABASE_URL=<Railway Postgres URL, normalized if required>`
  - `API_HOST=0.0.0.0` if still used after implementation
  - `API_PORT=<only if implementation intentionally maps this from PORT>`
- [ ] Populate `/app/db/chroma` by running ingestion on Railway from baked-in `data/bills/` and activating the generated vector store.
- [ ] Deploy backend and verify `/api/health` succeeds.
- [ ] Create the frontend service from the repo using `Dockerfile.frontend`.
- [ ] Set frontend variables exactly:
  - `VITE_API_BASE_URL=https://<backend-public-domain>`
- [ ] Deploy frontend and verify the UI loads from the Railway frontend domain.
- [ ] Run production smoke tests against the deployed app:
  - Health endpoint returns success.
  - Storage/vector-store endpoint shows an active ready vector store.
  - A narrow one-division query returns an answer and sources.
  - Citation hovers display source context.
  - Saved conversation reload preserves citation hovers through Chroma rehydration.
  - A CRX query shows original division metadata where applicable.
- [ ] Set Railway spending controls/usage alerts after services are confirmed working.
- [ ] Update this plan's Progress, Decisions, Discoveries, and Remaining Work sections after each meaningful implementation/deployment milestone.
- [ ] Commit implementation and docs changes in small logical commits without assistant attribution.

## Validation
Local validation before deploy:

```bash
python3 -m pytest tests/test_ingestion_service.py tests/test_rag_service_units.py tests/test_query_models.py
npm run build:frontend
docker-compose build backend frontend
```

Backend deployed validation:

```bash
curl -f https://<backend-public-domain>/api/health
```

Frontend deployed validation:

```bash
curl -f https://<frontend-public-domain>/health
```

Manual production smoke checks:
- Open `https://<frontend-public-domain>`.
- Submit a narrow query with one selected division.
- Confirm progress events stream until a final answer renders.
- Confirm source hovers render for returned citations.
- Save or reload the conversation and confirm source hovers still render.
- Submit one CRX-related query and confirm original source division metadata is visible where expected.

Railway operational checks:
- Backend logs show no missing `DATABASE_URL`, missing `OPENAI_API_KEY`, missing Chroma path, or CORS errors.
- Backend metrics do not show restart loops.
- Backend volume remains mounted after restart.
- Postgres service shows active connections from the backend.
- Railway usage estimate is reviewed after first successful smoke test.

## Documentation
Add or update a deployment section in `README.md` or a dedicated doc such as `docs/RAILWAY_DEPLOYMENT.md`.

The documentation must include:
- Required Railway services.
- Exact backend variables.
- Exact frontend variables.
- Chroma volume mount path.
- Chroma population method.
- Backend port/start-command behavior.
- Frontend API routing behavior.
- First deploy order.
- Smoke test checklist.
- Cost notes that storage is small and OpenAI usage is the main variable cost.

Do not include secret values in docs.

## Progress
2026-05-01 - Plan written. No implementation files changed.
2026-05-01 - User supplied deployment names and first-deploy choices: project `lawsearch`, default service names, Railway-generated domains, reingest Chroma on Railway, no custom domain, and GitHub auto-deploys. Backend exposure strategy remains open.
2026-05-01 - User approved `public-backend` as the first-deploy backend exposure strategy.
2026-05-01 - Implemented Railway readiness changes: backend Dockerfile uses `${PORT:-8000}`, frontend Dockerfile requires `VITE_API_BASE_URL` at build time, docker-compose passes a local frontend build arg, frontend production code rejects missing API base URL, backend settings normalize Railway/Postgres URLs and parse comma-separated `CORS_ORIGINS`, Railway deployment docs added, README linked.
2026-05-01 - Validation passed: `python3 -m pytest tests/test_ingestion_service.py tests/test_rag_service_units.py tests/test_query_models.py tests/test_config.py`, `npm run build:frontend`, and `docker-compose build backend frontend`.
2026-05-01 - Discovered that pydantic-settings decodes list env vars as JSON before validators run; fixed `CORS_ORIGINS` with `NoDecode` and added an env-backed regression test. Re-ran all validation successfully.

## Decisions
Use Railway as the primary deployment target.

Use separate backend, frontend, Postgres, and Chroma-volume responsibilities instead of combining all services into one container.

Keep the current RAG/model behavior unchanged for deployment.

Prefer explicit failure over fallback for missing production Chroma state, wrong vector-store root, or missing source rehydration data.

Use Railway-generated domains for the first deployment instead of configuring custom domains.

Use GitHub auto-deploys for the first deployment path.

Rebuild the Chroma vector store on Railway from source bills rather than uploading local `db/chroma`.

Use `public-backend` for the first deployment: frontend calls the backend Railway-generated public domain directly through `VITE_API_BASE_URL`, and backend CORS allows the frontend Railway-generated domain.

Use a Dockerfile shell `CMD` for backend startup so Railway's `PORT` variable expands correctly while local Docker Compose continues to default to `8000`.

Require `VITE_API_BASE_URL` during production frontend Docker builds so a Railway deployment cannot accidentally ship a localhost API URL.

Normalize `postgresql://` and `postgres://` database URLs to `postgresql+psycopg://` because this repo installs psycopg v3, not psycopg2.

## Discoveries
`Dockerfile.backend` currently hardcodes port `8000`.

`Dockerfile.frontend` currently proxies `/api/` to Docker Compose service DNS `http://backend:8000`.

`frontend/src/services/api.ts` falls back to `http://localhost:8000` when `VITE_API_BASE_URL` is absent.

`.dockerignore` excludes `db/chroma/`, so Chroma must be supplied through a persistent Railway volume or rebuilt in production.

The existing local `db/chroma/` directory is about `399M`; `data/` is about `5.8M`.

Railway Dockerfile services need `RAILWAY_DOCKERFILE_PATH` when the Dockerfile is not named root `Dockerfile`; this repo uses `Dockerfile.backend` and `Dockerfile.frontend`.

Railway-provided variables are available to frontend builds, but Dockerfile builds must declare variables with `ARG`; `Dockerfile.frontend` now declares `ARG VITE_API_BASE_URL`.

Comma-separated `CORS_ORIGINS` env values require `NoDecode`; otherwise pydantic-settings attempts JSON decoding before the field validator runs.

## Remaining Work
Create the Railway services, set variables/domains, mount the Chroma volume, run Railway ingestion, perform production smoke checks, set usage alerts, and commit the implementation/docs changes.
