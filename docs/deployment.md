# SevaQ Deployment Guide

This guide deploys `sevaq-public` as two services:

1. FastAPI backend
2. Streamlit dashboard

## 1) Local Docker Build and Run

From `sevaq-public/`:

### Build images

```bash
docker build -f Dockerfile.backend -t sevaq-backend:local .
docker build -f Dockerfile.dashboard -t sevaq-dashboard:local .
```

### Run backend

```bash
docker run --rm -p 8000:8000 \
  -e SEVAQ_DEMO_MODE=mock \
  sevaq-backend:local
```

Backend health check:

```bash
curl http://localhost:8000/health
```

### Run dashboard

```bash
docker run --rm -p 8501:8501 \
  -e SEVAQ_BACKEND_URL=http://host.docker.internal:8000 \
  sevaq-dashboard:local
```

Open: `http://localhost:8501`

## 2) Deploy Backend to Render or Railway

Use the `sevaq-public` repo/folder as the deployment source.

- **Dockerfile path:** `Dockerfile.backend`
- **Port:** `8000`
- **Start command:** defined in Dockerfile (`uvicorn app.main:app --port 8000`)

Recommended environment variables:

- `SEVAQ_DEMO_MODE=mock` (or `live`)
- `SEVAQ_TELEMETRY_DB_PATH=./sevaq_telemetry.db`
- If live OpenAI demo mode:
  - `OPENAI_API_KEY`
  - `SEVAQ_OPENAI_FAST_MODEL`
  - `SEVAQ_OPENAI_DEEP_MODEL`
  - `SEVAQ_OPENAI_VERIFIED_MODEL`
  - demo guardrails from `.env.example`
  - if model env vars are empty, low-cost defaults are used

Public-repo safety:

- Use `.env.example` as a template for local/env configuration
- Keep real secrets in `.env` or platform secret managers only
- Never commit `.env` to the public repository

Health endpoint:

- `GET /health`

## 3) Deploy Dashboard to Render or Railway

- **Dockerfile path:** `Dockerfile.dashboard`
- **Port:** `8501`
- **Start command:** defined in Dockerfile (`streamlit run ... --server.port=8501`)

Required environment variable:

- `SEVAQ_BACKEND_URL=https://<your-backend-domain>`

The dashboard already handles backend connection issues gracefully and shows connection status in the sidebar.

## 4) Custom Domain Mapping

Suggested mapping:

- Backend -> `api.sevaq.ai`
- Dashboard -> `demo.sevaq.ai`

After service deploy:

1. Add custom domain in your platform (Render/Railway).
2. Create DNS records in your domain provider:
   - `api.sevaq.ai` -> backend target
   - `demo.sevaq.ai` -> dashboard target
3. Verify TLS certificates are issued.
4. Set dashboard env:
   - `SEVAQ_BACKEND_URL=https://api.sevaq.ai`

## 5) Quick Production Checklist

- Backend `/health` returns `{"status":"ok"}`
- Dashboard sidebar shows backend connected
- CORS/network policy allows dashboard -> backend calls
- OpenAI keys/model env vars set only when using OpenAI mode
- Live demo may incur API costs; keep budget guardrails enabled
