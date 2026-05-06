# Sevaq Public

Adaptive reasoning infrastructure for safer, cost-aware AI execution.

## Live Demo

**Hosted demo:** [demo.sevaq.ai](https://demo.sevaq.ai)

The public deployment at `demo.sevaq.ai` showcases Sevaq end-to-end: adaptive routing, confidence guidance, and explainability signals.

## What Sevaq Does

Sevaq is an orchestration layer between user prompts and model providers. Instead of treating every request the same, it evaluates risk and complexity, selects a reasoning mode, and returns both output and operational context (why that mode was selected, what validation was applied, and what compute posture was used).

## Why Adaptive Reasoning Matters

Most AI pipelines either over-spend on easy prompts or under-protect high-stakes prompts. Sevaq addresses both failure modes by adapting execution strategy per request:

- lower latency/cost for low-risk work
- deeper reasoning for complex planning tasks
- higher caution and verification posture for sensitive domains

## Core Concepts

### FAST

Low-latency path for straightforward, low-risk tasks where responsiveness and efficiency are prioritized.

### DEEP

Higher-effort path for complex prompts that benefit from richer reasoning and structured synthesis.

### VERIFIED

Caution-oriented path for high-stakes or sensitive prompts, emphasizing uncertainty handling and external verification signals.

### Validation

A public-safe validation layer annotates outputs with confidence posture, risk flags, and recommendations for external verification when appropriate.

Current public verifier behavior is heuristic and is designed as a confidence-signal layer, not a factual correctness guarantee. Future verifier implementations may add LLM review, retrieval grounding, citation checks, and multi-agent review.

### Control Metrics

Each execution reports estimated cost/latency and compute-intensity allocation signals so operators can evaluate risk-adjusted efficiency.

### Provider-Agnostic Orchestration

Sevaq keeps orchestration logic decoupled from any single model provider. Public mode includes mock and OpenAI-backed options; private policy/provider plugins can be layered in separately.

## Demo Experience

The hosted experience includes:

- **Founder Demo**: curated product narrative focused on differentiation and business value
- **User Preview (Live)**: live user-facing flow powered by the backend
- **User Story (Static)**: controlled showcase moments for stakeholder storytelling

Each view is designed to make adaptive behavior legible for non-technical audiences while preserving technical credibility.

## Architecture Overview

Sevaq is composed of:

- **API layer** (`FastAPI`) for routing and execution endpoints
- **Orchestration layer** for probe -> route -> profile -> provider selection
- **Validation layer** for public-safe caution and verification annotations
- **Telemetry layer** (`SQLite` in public setup) for execution observability
- **Dashboard layer** (`Streamlit`) for live demo interaction and evidence

## Example Scenarios

- Simple drafting -> expected **FAST**
- Architecture planning -> expected **DEEP**
- Medical/legal/financial prompts -> expected **VERIFIED**
- Factual trap prompts -> caution-oriented validation posture

The demo includes curated scenarios to make these transitions observable in a consistent way.

## Deployment Overview

Sevaq is typically deployed as two services:

1. FastAPI backend (`api`)
2. Streamlit dashboard (`demo`)

For Docker and cloud deployment details (Render/Railway-style setups), see `docs/deployment.md`.

## Optional Self-Hosting / Local Development

Local setup is optional if you only want the hosted demo.

### Environment Setup (Public Repo Safe)

Use `.env.example` as your template and keep local secrets in `.env` only:

`cp .env.example .env`

`.env` is ignored by git and should never be committed to the public repository.

### Install

`python3 -m venv .venv`

`source .venv/bin/activate`

`python -m pip install -r backend/requirements.txt`

`python -m pip install -r dashboard/requirements.txt`

or

`make install`

### Run

Backend (default mock mode):

`SEVAQ_DEMO_MODE=mock uvicorn --app-dir backend app.main:app --reload`

Backend (live mode with OpenAI):

`SEVAQ_DEMO_MODE=live OPENAI_API_KEY=... SEVAQ_OPENAI_FAST_MODEL=... SEVAQ_OPENAI_DEEP_MODEL=... SEVAQ_OPENAI_VERIFIED_MODEL=... uvicorn --app-dir backend app.main:app --reload`

Dashboard:

`streamlit run dashboard/streamlit_app.py`

Optional live guardrails:

- `SEVAQ_MAX_PROMPT_CHARS`
- `SEVAQ_OPENAI_MAX_OUTPUT_TOKENS`
- `SEVAQ_OPENAI_REQUEST_TIMEOUT_SECONDS`
- `SEVAQ_OPENAI_DAILY_COST_BUDGET_UNITS`
- `SEVAQ_OPENAI_GUARDRAIL_FALLBACK_TO_MOCK` (`true` by default)

## Tests

Run full suite:

`pytest -q tests`

or

`make test`

## Disclaimer

Sevaq Public is a public-safe demonstration of adaptive reasoning orchestration and operational controls. It is not legal, medical, immigration, or financial advice. High-stakes outputs should be independently verified with qualified human experts and trusted primary sources.
