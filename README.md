# Sevaq Public

Adaptive reasoning infrastructure for safer, cost-aware AI execution.

---

# Live Demo

Hosted demo: `demo.sevaq.ai`

The public deployment showcases Sevaq end-to-end:
- adaptive reasoning selection
- confidence-aware execution
- explainable routing behavior
- operational telemetry and validation posture

Sevaq is designed to make AI execution strategy observable rather than opaque.

---

# What Sevaq Does

Sevaq is an orchestration and execution control layer between user prompts and model providers.

Instead of treating every request the same, Sevaq:
1. evaluates prompt complexity and risk posture
2. selects an execution strategy
3. applies reasoning and validation policies
4. returns both output and execution context

This includes:
- why a reasoning mode was selected
- what validation posture was applied
- estimated compute intensity
- confidence and caution annotations
- external verification recommendations when appropriate

The goal is not only to generate responses, but to make AI reasoning posture legible and governable.

---

# Why Adaptive Reasoning Matters

Most AI systems fail in one of two ways:
- over-spending compute on trivial tasks
- under-protecting high-stakes tasks

Sevaq addresses both failure modes by dynamically adapting execution strategy per request.

Examples:
- lower latency and lower cost for routine prompts
- deeper reasoning for complex planning and synthesis
- higher caution and verification posture for sensitive domains

Sevaq treats reasoning allocation as a runtime decision rather than a static model configuration.

---

# Core Reasoning Modes

## FAST

Low-latency execution path for straightforward, low-risk tasks where responsiveness and efficiency are prioritized.

Typical characteristics:
- short reasoning window
- lightweight execution
- cost-efficient routing
- minimal validation overhead

Example use cases:
- drafting
- summarization
- lightweight transformations
- simple Q&A

---

## DEEP

Higher-effort execution path for prompts requiring decomposition, multi-step reasoning, tradeoff analysis, or structured synthesis.

DEEP mode may apply:
- staged reasoning
- prompt decomposition
- iterative synthesis
- expanded reasoning windows
- higher compute allocation
- structured response generation

Example use cases:
- architecture design
- planning workflows
- technical analysis
- multi-step problem solving

---

## VERIFIED

Caution-oriented execution path for high-stakes or sensitive prompts.

VERIFIED prioritizes uncertainty visibility over response fluency when confidence is low or external validation is recommended.

The public implementation emphasizes:
- uncertainty handling
- caution signaling
- verification recommendations
- risk annotations
- confidence posture guidance

Future verifier implementations may include:
- retrieval grounding
- citation validation
- cross-model review
- adversarial critique
- multi-agent verification

Example use cases:
- financial guidance
- legal workflows
- healthcare-adjacent prompts
- policy-sensitive reasoning

---

# Explainable Execution

Sevaq exposes execution posture alongside model output.

Each execution may include:
- selected reasoning mode
- estimated compute intensity
- latency and cost signals
- validation posture
- confidence annotations
- caution indicators
- escalation recommendations

This allows operators to inspect not only what the system answered, but how the system chose to reason.

---

# Validation Layer

The public validation layer is intentionally public-safe and conservative.

Current verifier behavior is heuristic and designed as a confidence-signal layer rather than a factual correctness guarantee.

The system is designed to surface:
- uncertainty
- ambiguity
- caution conditions
- validation recommendations

rather than simulate false certainty.

---

# Control Metrics

Each execution reports operational metrics including:
- estimated latency
- estimated compute intensity
- estimated cost posture
- reasoning mode allocation

These signals allow operators to evaluate:
- risk-adjusted efficiency
- runtime behavior
- reasoning allocation tradeoffs
- cost vs validation posture

---

# Provider-Agnostic Orchestration

Sevaq keeps orchestration logic decoupled from any single model provider.

Public mode currently supports:
- mock execution
- OpenAI-backed execution

The orchestration layer is designed to support:
- provider abstraction
- policy-driven routing
- configurable execution strategies
- pluggable validation layers

Private provider and policy plugins can be layered independently.

---

# Demo Experience

The hosted experience currently includes:

### Executive Walkthrough
Curated narrative focused on product positioning, adaptive reasoning behavior, and operational differentiation.

### User Preview (Live)
Live user-facing execution flow powered by the backend runtime.

### User Story (Static)
Controlled showcase scenarios for stakeholder demonstrations and repeatable storytelling.

The demo is designed to make adaptive execution behavior legible for both technical and non-technical audiences.

---

# Architecture Overview

Sevaq is composed of:

- API layer (`FastAPI`) for routing and execution endpoints
- Orchestration layer for probe → route → profile → provider selection
- Policy layer for execution controls and routing posture
- Validation layer for caution and verification annotations
- Telemetry layer (`SQLite` in public mode) for execution observability
- Dashboard layer (`Streamlit`) for interactive demonstrations

---

# Execution Flow

```text
User Prompt
     ↓
Risk / Complexity Probe
     ↓
FAST | DEEP | VERIFIED
     ↓
Validation Layer
     ↓
Output + Execution Context
     ↓
Telemetry / Audit Signals
```

---

# Example Scenarios

| Scenario | Expected Mode |
|---|---|
| Simple drafting | FAST |
| Architecture planning | DEEP |
| Financial or legal prompts | VERIFIED |
| Factual trap prompts | VERIFIED |
| Multi-step synthesis | DEEP |

The demo includes curated scenarios to make execution transitions observable and repeatable.

---

# Deployment Overview

Sevaq is typically deployed as two services:

1. FastAPI backend (`api`)
2. Streamlit dashboard (`demo`)

For Docker and cloud deployment details, see:

`docs/deployment.md`

---

# Optional Self-Hosting / Local Development

Local setup is optional if you only want the hosted demo.

---

# Environment Setup (Public Repo Safe)

Use `.env.example` as your template and keep secrets in `.env` only.

```bash
cp .env.example .env
```

`.env` is ignored by git and should never be committed publicly.

---

# Install

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r backend/requirements.txt
python -m pip install -r dashboard/requirements.txt
```

or:

```bash
make install
```

---

# Run

## Backend (mock mode)

```bash
SEVAQ_DEMO_MODE=mock uvicorn --app-dir backend app.main:app --reload
```

## Backend (live mode)

```bash
SEVAQ_DEMO_MODE=live \
OPENAI_API_KEY=... \
SEVAQ_OPENAI_FAST_MODEL=... \
SEVAQ_OPENAI_DEEP_MODEL=... \
SEVAQ_OPENAI_VERIFIED_MODEL=... \
uvicorn --app-dir backend app.main:app --reload
```

## Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

---

# Optional Runtime Guardrails

```text
SEVAQ_MAX_PROMPT_CHARS
SEVAQ_OPENAI_MAX_OUTPUT_TOKENS
SEVAQ_OPENAI_REQUEST_TIMEOUT_SECONDS
SEVAQ_OPENAI_DAILY_COST_BUDGET_UNITS
SEVAQ_OPENAI_GUARDRAIL_FALLBACK_TO_MOCK
```

---

# Tests

Run the full suite:

```bash
pytest -q tests
```

or:

```bash
make test
```

---

# Disclaimer

Sevaq Public is a public-safe demonstration of adaptive reasoning orchestration, execution governance, and operational controls.

It is not legal, medical, immigration, or financial advice.

High-stakes outputs should always be independently verified with qualified experts and trusted primary sources.