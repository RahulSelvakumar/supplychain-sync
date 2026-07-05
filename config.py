import os
from dotenv import load_dotenv

load_dotenv()

# ── Google Cloud ───────────────────────────────────────────────────────────────
GCP_PROJECT  = "supplychain-sync-hackathon"
GCP_LOCATION = "us-central1"

# ── BigQuery ───────────────────────────────────────────────────────────────────
BQ_DATASET    = "supply_chain"
BQ_TABLE      = "shipments"
BQ_FULL_TABLE = f"{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
BQ_TOTAL_ROWS = 500_000

# ── AI Models ──────────────────────────────────────────────────────────────────
GEMINI_MODEL     = "gemini-2.5-flash"
NVIDIA_NIM_URL   = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_NIM_MODEL = "google/gemma-2-2b-it"

# ── Demo Alert ─────────────────────────────────────────────────────────────────
ALERT_TEXT = "Port Strike Detected (Singapore Hub) - 5 Million Active Records at Risk"
