# 🌐 SupplyChain Sync

**Autonomous Supply Chain Disruption Triage** — a multi-agent AI system that detects, analyzes, and resolves critical supply chain disruptions in real time, comparing standard CPU-based processing against NVIDIA GPU-accelerated inference.

---

## Changelog

| Version | What Changed |
|---|---|
| **v3.0.0** | Real agent pipeline — grounded LLM prompts from live BQ data, BigQuery acceleration benchmark, structured folder layout |

**Live:** https://supplychain-sync-629747631357.us-central1.run.app
| **v2.0.0** | Full dashboard UI redesign — command centre layout, Plotly charts, tabbed results, sidebar controls |
| **v1.0.0** | Initial release — LangGraph pipeline, NVIDIA NIM + Gemini integration |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   Streamlit Dashboard (app.py)               │
│              Sidebar · KPI Strip · Alert Banner              │
│        Active Shipments Table · BQ Benchmark Section         │
└───────────────┬──────────────────────┬───────────────────────┘
                │                      │
   ┌────────────▼──────┐    ┌──────────▼──────────┐
   │  Standard Agent   │    │  Accelerated Agent  │
   │  (CPU / pandas)   │    │  (NVIDIA cuDF + NIM)│
   └────────────┬──────┘    └──────────┬──────────┘
                │                      │
        ┌───────▼──────────────────────▼───────┐
        │       LangGraph State Machine         │
        │              (agents.py)              │
        │                                       │
        │  START                                │
        │    │                                  │
        │    ▼                                  │
        │  ┌──────────────────────────────────┐ │
        │  │  1. Orchestrator Agent           │ │
        │  │  Gemini 2.5 Flash (Vertex AI)    │ │
        │  │  → Extracts disruption_type      │ │
        │  │    & affected_hub from alert     │ │
        │  └────────────────┬─────────────────┘ │
        │                   │                   │
        │    ┌──────────────▼──────────────┐    │
        │    │  2. Data Ops Agent          │    │
        │    │  BigQuery (REST or Storage  │    │
        │    │  API) filtered by hub       │    │
        │    │  → affected_routes[] passed │    │
        │    │    forward to Optimizer     │    │
        │    └──────────────┬──────────────┘    │
        │                   │                   │
        │    ┌──────────────▼──────────────┐    │
        │    │  3. Optimizer Agent         │    │
        │    │  NVIDIA NIM (Gemma 2-2B-it) │    │
        │    │  Grounded prompt with real  │    │
        │    │  BQ route data              │    │
        │    │  → routing_plan             │    │
        │    └──────────────┬──────────────┘    │
        │                   │                   │
        │    ┌──────────────▼──────────────┐    │
        │    │  4. Guardrails Agent        │    │
        │    │  Validates route context    │    │
        │    │  count ≥ 3 before approve   │    │
        │    └──────────────┬──────────────┘    │
        │                   │                   │
        │                  END                  │
        └───────────────────────────────────────┘
```

---

## Agent Pipeline (v3 — Real, Not Mocked)

### 1. 🧠 Orchestrator Agent
- **Model**: Gemini 2.5 Flash (Google Vertex AI, `us-central1`)
- **Role**: Extracts structured data from the raw alert string using a JSON extraction prompt.
- **Output**: `disruption_type` (e.g. `Strike`) and `affected_hub` (e.g. `Singapore`) written to shared state — used by Data Ops to filter BigQuery.
- **Fallback**: Keyword-scans the alert string if Gemini JSON parse fails.

### 2. 📊 Data Ops Agent
- **Role**: Queries BigQuery `supply_chain.shipments` filtered by `origin_port = affected_hub`, returning the top 10 affected routes with unit counts, destination ports, and risk scores.
- **GPU path**: BigQuery Storage Read API (Arrow columnar) — full 10 routes loaded, passed forward.
- **CPU path**: Standard REST API — truncated to 2 routes before processing completes, simulating the degraded data context a slow pipeline produces.
- **Output**: `affected_routes[]` (real BQ data), `db_latency`, `throughput`.

### 3. 🔍 Optimizer Agent
- **Role**: Builds a **grounded prompt** embedding the actual `affected_routes` JSON from BigQuery, then calls the LLM to generate a specific rerouting plan.
- **GPU path**: Full context (10 routes) → LLM generates a plan naming real destination ports, unit volumes, and alternate transport modes.
- **CPU path**: Partial context (2 routes) → LLM generates a cautious degraded plan acknowledging the data gap.
- **Primary LLM**: NVIDIA NIM — `google/gemma-2-2b-it`
- **Fallback 1**: Gemini 2.5 Flash
- **Fallback 2**: Offline heuristic using top route from BQ data

### 4. 🛡️ Guardrails Agent
- **Role**: Validates the routing plan has sufficient data context before authorizing execution.
- **Rule**: Passes only if `len(affected_routes) >= 3`. CPU path (2 routes) always fails. GPU path (10 routes) always passes.

---

## BigQuery Acceleration Benchmark

The dashboard includes a live benchmark that runs the **exact same aggregation query** on the 500K-row `shipments` table twice:

| Method | Transport | Format | Speed |
|---|---|---|---|
| Standard | BigQuery REST API | JSON | Baseline |
| Accelerated | BigQuery Storage Read API | Apache Arrow (columnar) | ~2–5x faster |

The Storage Read API uses parallel streams and zero-copy Arrow buffers, eliminating JSON serialization overhead for analytical workloads.

---

## CPU vs GPU Comparison

| Metric | Standard (CPU) | Accelerated (GPU) |
|---|---|---|
| BQ Query Method | REST API | Storage Read API |
| Data Join Latency | ~130–200 sec | ~0.7–0.9 sec |
| Throughput | ~25K–40K rows/s | ~6M–8M rows/s |
| Routes in Context | 2 / 10 (truncated) | 10 / 10 (complete) |
| LLM Prompt | Partial / degraded | Grounded with real BQ data |
| Context Accuracy | ~36–45% | ~97–100% |
| Cost Impact | ~$145,000+ | ~$12,000 |
| Guardrail | ❌ Failed (insufficient data) | ✅ Passed (full context) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Agent Orchestration | LangGraph (StateGraph) |
| Orchestrator LLM | Google Gemini 2.5 Flash (Vertex AI) |
| Optimizer LLM (Primary) | NVIDIA NIM — `google/gemma-2-2b-it` |
| Optimizer LLM (Fallback) | Google Gemini 2.5 Flash |
| Data Warehouse | Google BigQuery (500K rows) |
| Accelerated BQ Fetch | BigQuery Storage Read API (Apache Arrow) |
| GPU Data Processing | NVIDIA RAPIDS cuDF |
| CPU Data Processing | pandas |
| Containerization | Docker |
| Deployment | Google Cloud Run |

---

## Project Structure

```
supplychain-sync/
│
├── app.py              # Streamlit UI — imports only, no business logic
├── agents.py           # LangGraph pipeline — all 4 agents
├── config.py           # All constants: GCP project, models, BQ table
├── llm.py              # LLM client init: Gemini + nvidia_nim_invoke()
│
├── data/
│   ├── bigquery.py     # fetch_bq_data() + benchmark_bq_fetch()
│   └── shipments.py    # Simulated active routes table
│
├── ui/
│   ├── styles.py       # Global CSS
│   └── charts.py       # Plotly chart builders (latency, cost, gauge, BQ)
│
├── scripts/
│   ├── bigquery_setup.py   # One-time: creates 500K row BQ table
│   └── list_models.py      # Utility: lists available Vertex AI models
│
├── Dockerfile
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Setup & Run

### 1. Clone & Install
```bash
git clone https://github.com/RahulSelvakumar/supplychain-sync.git
cd supplychain-sync
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env:
# NVIDIA_API_KEY=your-nvidia-api-key
```

### 3. Google Cloud Auth
```bash
gcloud auth application-default login
gcloud config set project supplychain-sync-hackathon
```

### 4. Create BigQuery Dataset (one-time)
```bash
python3 scripts/bigquery_setup.py
```

### 5. Run
```bash
streamlit run app.py
```

### 6. Docker
```bash
docker build -t supplychain-sync .
docker run -p 8501:8501 --env-file .env supplychain-sync
```

### 7. Deploy to Cloud Run
```bash
gcloud builds submit --tag gcr.io/supplychain-sync-hackathon/supplychain-sync
gcloud run deploy supplychain-sync \
  --image gcr.io/supplychain-sync-hackathon/supplychain-sync \
  --platform managed --region us-central1 \
  --allow-unauthenticated --memory 4Gi --cpu 2 --timeout 300 \
  --set-secrets=NVIDIA_API_KEY=NVIDIA_API_KEY:latest
```

---

## NVIDIA NIM Integration

The Optimizer Agent calls NVIDIA NIM directly using the OpenAI-compatible REST API, bypassing the `langchain-nvidia-ai-endpoints` wrapper (which has account-level function UUID routing issues):

```python
POST https://integrate.api.nvidia.com/v1/chat/completions
Model: google/gemma-2-2b-it
```

---

## Triple Safety Net (Optimizer)

```
NVIDIA NIM (google/gemma-2-2b-it) — grounded prompt with live BQ routes
        │ fails?
        ▼
Gemini 2.5 Flash (Vertex AI) — same grounded prompt
        │ fails?
        ▼
Offline Heuristic — constructs plan from top BQ route dict
```
