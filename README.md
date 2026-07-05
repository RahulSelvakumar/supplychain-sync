# 🌐 SupplyChain Sync

**Autonomous Supply Chain Disruption Triage** — a multi-agent AI system that detects, analyzes, and resolves critical supply chain disruptions in real time, comparing standard CPU-based processing against NVIDIA GPU-accelerated inference.

---

## Architecture Overview

```
                        ┌─────────────────────────────────────┐
                        │         Streamlit Dashboard         │
                        │  app.py — Side-by-side comparison   │
                        └────────────┬──────────┬─────────────┘
                                     │          │
                     ┌───────────────▼──┐    ┌──▼───────────────┐
                     │  Standard Agent  │    │ Accelerated Agent│
                     │  (CPU / Legacy)  │    │ (NVIDIA cuDF+NIM)│
                     └───────────────┬──┘    └──┬───────────────┘
                                     │          │
                        ┌────────────▼──────────▼────────────┐
                        │       LangGraph State Machine      │
                        │         (agents.py)                │
                        │                                    │
                        │  START                             │
                        │    │                               │
                        │    ▼                               │
                        │  ┌─────────────────┐               │
                        │  │  Orchestrator   │ ◄── Gemini    │
                        │  │     Agent       │     2.5 Flash │
                        │  └────────┬────────┘  (Vertex AI)  │
                        │           │                        │
                        │           ▼                        │
                        │  ┌─────────────────┐               │
                        │  │   Data Ops      │ ◄── pandas    │
                        │  │     Agent       │     (CPU) or  │
                        │  └────────┬────────┘  cudf (GPU)   │
                        │           │                        │
                        │           ▼                        │
                        │  ┌─────────────────┐               │
                        │  │   Optimizer     │ ◄── NVIDIA NIM│
                        │  │     Agent       │  (Gemma 2-2B) │
                        │  └────────┬────────┘  + Gemini     │
                        │           │             fallback   │
                        │           ▼                        │
                        │  ┌─────────────────┐               │
                        │  │   Guardrails    │               │
                        │  │     Agent       │               │
                        │  └────────┬────────┘               │
                        │           │                        │
                        │          END                       │
                        └────────────────────────────────────┘
```

---

## Agent Pipeline

### 1. 🧠 Orchestrator Agent
- **Model**: Gemini 2.5 Flash (Google Vertex AI, `us-central1`)
- **Role**: Receives the raw disruption alert and categorizes it into a single-word disruption type (e.g., `Strike`, `Flood`, `Shortage`).
- **Fallback**: Logs error and continues pipeline gracefully if Vertex AI is unavailable.

### 2. 📊 Data Ops Agent
- **Role**: Simulates an ETL join across ~5.25 million active supply chain records.
- **CPU path**: Uses standard `pandas` — slow (~130–200 sec latency), data truncation detected.
- **GPU path**: Uses NVIDIA `cudf.pandas` — 6–8M rows/sec throughput, sub-second latency.
- **Output**: `db_latency`, `throughput` metrics written to shared agent state.

### 3. 🔍 Optimizer Agent
- **Role**: Drafts a specific, actionable 1-sentence routing plan based on the disruption alert.
- **Primary (GPU path)**: NVIDIA NIM API — `google/gemma-2-2b-it` via direct OpenAI-compatible REST call.
- **Fallback 1**: Gemini 2.5 Flash (Vertex AI) if NVIDIA NIM fails.
- **Fallback 2**: Hardcoded offline heuristic if both live APIs are unreachable.
- **CPU path**: Returns a generic truncation warning (no live inference due to data loss).

### 4. 🛡️ Guardrails Agent
- **Role**: Validates the routing plan against safety and budget policies.
- **GPU path**: Passes (data complete, high-accuracy plan).
- **CPU path**: Fails (data truncated, plan unsafe for execution).

---

## CPU vs GPU Comparison

| Metric | Standard (CPU) | Accelerated (GPU) |
|---|---|---|
| Data Join Latency | ~130–200 sec | ~0.7–0.9 sec |
| Throughput | ~25K–40K rows/s | ~6M–8M rows/s |
| Context Accuracy | ~36–45% | ~97–100% |
| Cost Impact | ~$145,000+ | ~$12,000 |
| Routing Plan | Generic halt warning | Precise air freight re-route |
| Guardrail | ❌ Failed | ✅ Passed |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Agent Orchestration | LangGraph (StateGraph) |
| Orchestrator LLM | Google Gemini 2.5 Flash (Vertex AI) |
| Optimizer LLM (Primary) | NVIDIA NIM — `google/gemma-2-2b-it` |
| Optimizer LLM (Fallback) | Google Gemini 2.5 Flash |
| GPU Data Processing | NVIDIA RAPIDS cuDF |
| CPU Data Processing | pandas |
| Containerization | Docker |

---

## Project Structure

```
supplychain-sync/
├── app.py               # Streamlit dashboard — side-by-side CPU vs GPU demo
├── agents.py            # LangGraph multi-agent pipeline (all 4 agents)
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container definition
├── .env.example         # Environment variable template
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
# Edit .env and add your keys:
# NVIDIA_API_KEY=your-nvidia-api-key
```

You also need Google Cloud credentials with Vertex AI access:
```bash
gcloud auth application-default login
```

### 3. Run
```bash
streamlit run app.py
```

### 4. Docker
```bash
docker build -t supplychain-sync .
docker run -p 8501:8501 --env-file .env supplychain-sync
```

---

## NVIDIA NIM Integration

The Optimizer Agent calls NVIDIA NIM directly using the OpenAI-compatible REST API:

```python
POST https://integrate.api.nvidia.com/v1/chat/completions
Model: google/gemma-2-2b-it
```

This bypasses the `langchain-nvidia-ai-endpoints` wrapper (which has account-level function UUID issues) and calls the endpoint directly, exactly as shown in the official NVIDIA NIM docs.

---

## Triple Safety Net (Optimizer)

```
NVIDIA NIM (google/gemma-2-2b-it)
        │ fails?
        ▼
Gemini 2.5 Flash (Vertex AI)
        │ fails?
        ▼
Offline Heuristic (hardcoded emergency route)
```
