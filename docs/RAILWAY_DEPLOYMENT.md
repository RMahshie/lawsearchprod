# Railway Deployment

This app deploys to Railway as separate services in one project named `lawsearch`.

## Services

Create these Railway services:

| Railway service | Source | Required setting |
| --- | --- | --- |
| `lawsearch-postgres` | Railway Postgres template | Managed Postgres database |
| `lawsearch-backend` | GitHub repo | `RAILWAY_DOCKERFILE_PATH=Dockerfile.backend` |
| `lawsearch-frontend` | GitHub repo | `RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend` |

Attach one Railway volume to `lawsearch-backend`:

| Volume purpose | Mount path |
| --- | --- |
| Chroma vector stores | `/app/db/chroma` |

Use Railway-generated domains for the first deployment. Generate public domains for both `lawsearch-backend` and `lawsearch-frontend`.

## Backend Variables

Set these variables on `lawsearch-backend`:

```text
RAILWAY_DOCKERFILE_PATH=Dockerfile.backend
OPENAI_API_KEY=<secret>
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATA_DIR=/app/data/bills
VECTORSTORE_DIR=/app/db/chroma
DATABASE_URL=${{lawsearch-postgres.DATABASE_URL}}
CORS_ORIGINS=https://<frontend-railway-domain>
```

Do not set `PORT`. Railway provides it. The backend container starts Uvicorn on `${PORT:-8000}`.

`DATABASE_URL` may be supplied by Railway as `postgresql://...` or `postgres://...`; the app normalizes those schemes to `postgresql+psycopg://...` at startup.

## Frontend Variables

Set these variables on `lawsearch-frontend`:

```text
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
VITE_API_BASE_URL=https://<backend-railway-domain>
```

`VITE_API_BASE_URL` is required during the Docker build. The production frontend will not fall back to localhost.

## First Deploy Order

1. Create Railway project `lawsearch`.
2. Add `lawsearch-postgres`.
3. Add `lawsearch-backend` from the GitHub repo.
4. Set `RAILWAY_DOCKERFILE_PATH=Dockerfile.backend` on `lawsearch-backend`.
5. Attach the backend volume at `/app/db/chroma`.
6. Set all backend variables except `CORS_ORIGINS`.
7. Deploy backend and generate its Railway public domain.
8. Add `lawsearch-frontend` from the GitHub repo.
9. Set `RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend`.
10. Set `VITE_API_BASE_URL` to the backend public domain.
11. Deploy frontend and generate its Railway public domain.
12. Set backend `CORS_ORIGINS` to the frontend public domain.
13. Redeploy backend so CORS takes effect.
14. Rebuild Chroma on Railway from the baked-in source bills.
15. Run the production smoke checks.

## Rebuild Chroma On Railway

After backend deploy succeeds and the volume is mounted, create and activate a fresh vector store from the deployed source bills:

```bash
curl -X POST "https://<backend-railway-domain>/api/storage/vector-stores" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Railway FY2026",
    "embedding_model": "text-embedding-3-large",
    "chunk_size": 1500,
    "chunk_overlap": 200,
    "activate": true
  }'
```

Then verify the active store:

```bash
curl -f "https://<backend-railway-domain>/api/storage/vector-stores"
```

## Smoke Checks

Run these checks after both services are deployed:

```bash
curl -f "https://<backend-railway-domain>/api/health"
curl -f "https://<frontend-railway-domain>/health"
```

Manual checks:

- Open `https://<frontend-railway-domain>`.
- Submit a narrow one-division query.
- Confirm streaming progress reaches a final answer.
- Confirm citation hovers show source context.
- Reload a saved conversation and confirm citation hovers still work.
- Submit one CRX-related query and confirm original division metadata appears where applicable.

Railway checks:

- Backend logs have no missing `OPENAI_API_KEY`, `DATABASE_URL`, Chroma path, or CORS errors.
- Backend does not restart-loop.
- Backend volume remains mounted after redeploy.
- Postgres shows active backend connections.

## Cost Notes

The source bills are small and the local Chroma store has been under 1 GB. Railway volume storage should be minor compared with always-on backend/database compute and OpenAI API calls.

Set Railway usage alerts or a spending limit after the first successful smoke test.
