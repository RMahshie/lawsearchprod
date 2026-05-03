# Setup Guide

This project runs as a Dockerized FastAPI backend and React frontend. You need Docker, Node/npm for local frontend work, Python 3.11+ for local backend work, and an OpenAI API key.

## Environment

Create `.env` from the example file:

```bash
cp .env.example .env
```

Set:

```bash
OPENAI_API_KEY=sk-your-key
```

Optional settings include `LAWSEARCH_MODEL_PROFILE=openai|deepseek`, `DEEPSEEK_API_KEY`, `EMBEDDING_MODEL`, `API_HOST`, `API_PORT`, `LOG_LEVEL`, `ENVIRONMENT`, and `DEBUG=true`.

Use `LAWSEARCH_MODEL_PROFILE=deepseek` to run chat stages with the DeepSeek comparison profile. `OPENAI_API_KEY` is still required for OpenAI embeddings and for any OpenAI chat slots in the active profile.

## Docker Run

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs

For development hot reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Local Development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm run dev:backend
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Run both from the repository root:

```bash
npm run dev
```

## Tests and Checks

```bash
python3 -m pytest
npm run lint:frontend
npm run build:frontend
```

## Ingestion Notes

The UI can rebuild Chroma with a selected embedding model and chunk size. Chroma persists under `db/chroma/`, and the active embedding model is recorded in `db/chroma/.embedding_model` to avoid dimension mismatches.
