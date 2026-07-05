import streamlit as st
from datetime import datetime

from agents import workflow
from config import ALERT_TEXT
from data.bigquery import fetch_bq_data, benchmark_bq_fetch
from data.shipments import get_shipment_data
from ui.styles import CSS
from ui.charts import latency_chart, cost_chart, accuracy_gauge, throughput_chart, bq_risk_chart, bq_fetch_chart

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupplyChain Sync | Command Center",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌐 SupplyChain Sync")
    st.caption("Autonomous Disruption Command Center")
    st.divider()

    st.markdown('<div class="section-label">Active Incident</div>', unsafe_allow_html=True)
    st.error("🔴 **PORT STRIKE — Singapore Hub**\n\nDetected: 05 Jul 2026, 07:24 UTC\n\n5.25M records at risk across 3 routes")

    st.markdown('<div class="section-label">AI Engine Stack</div>', unsafe_allow_html=True)
    st.markdown("""
| Agent | Model |
|---|---|
| 🧠 Orchestrator | Gemini 2.5 Flash |
| 🔍 Optimizer | Gemma 2-2B · NIM |
| 📊 Data Engine | RAPIDS cuDF |
| 🛡️ Guardrails | Rule-based |
""")
    st.divider()
    run_triage = st.button("⚡ Run AI Triage", type="primary", use_container_width=True)
    st.divider()

    st.markdown('<div class="section-label">Hub Status</div>', unsafe_allow_html=True)
    st.markdown("""
- 🟢 Rotterdam Hub — Nominal
- 🟢 Los Angeles Hub — Nominal
- 🔴 Singapore Hub — **Disrupted**
- 🟢 Hamburg Hub — Nominal
- 🟢 Shanghai Hub — Nominal
""")

# ── Header ─────────────────────────────────────────────────────────────────────
hdr_col, ts_col = st.columns([3, 1])
with hdr_col:
    st.markdown("## Supply Chain Command Center")
    st.caption("Real-time AI disruption triage · Google Vertex AI + NVIDIA NIM")
with ts_col:
    st.markdown(
        f"<div style='text-align:right;padding-top:10px;color:#8892b0;font-size:0.8rem;'>"
        f"Last updated<br><b style='color:#cdd;font-size:0.95rem;'>"
        f"{datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}</b></div>",
        unsafe_allow_html=True,
    )

# ── KPI Strip ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Active Routes",    "8",        delta="3 disrupted",      delta_color="inverse")
k2.metric("Units at Risk",    "5.25M",    delta="Singapore hub",    delta_color="inverse")
k3.metric("Cost Exposure",    "$145,000", delta="If unresolved",    delta_color="inverse")
k4.metric("AI Agents Online", "4 / 4",   delta="All systems ready")
st.divider()

# ── Alert Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="alert-critical">
  <div class="alert-title">🚨 CRITICAL INCIDENT — PORT STRIKE: Singapore PSA Terminals</div>
  <div class="alert-body">
    Industrial action has halted all container operations at Singapore PSA terminals.
    Routes SG-001, SG-002 &amp; MY-007 are directly affected · 5,250,000 active records blocked ·
    Estimated delay: 7–14 days without AI re-routing.
  </div>
</div>
""", unsafe_allow_html=True)

# ── Active Shipments Table ─────────────────────────────────────────────────────
st.markdown('<div class="section-label">Active Shipment Routes</div>', unsafe_allow_html=True)
st.dataframe(get_shipment_data(), use_container_width=True, hide_index=True, height=290)

# ── BigQuery Live Data Section ─────────────────────────────────────────────────
st.markdown('<div class="section-label">BigQuery Data Layer — 500K Live Shipment Records</div>', unsafe_allow_html=True)

bq_btn_col, bq_desc_col = st.columns([1, 5])
fetch_bq = bq_btn_col.button("🔍 Fetch from BigQuery", use_container_width=True)
bq_desc_col.caption(
    "Runs the **same aggregation query** twice on 500K rows · "
    "Standard REST API vs Accelerated BigQuery Storage Read API (Arrow columnar)"
)

if fetch_bq:
    # ── Step 1: Standard REST API ───────────────────────────────────────────
    with st.status("🐌 Step 1 — Fetching via Standard BigQuery REST API...", expanded=True) as s1:
        from data.bigquery import benchmark_bq_fetch as _bench
        std_time, storage_time, rows, err = _bench()
        if err:
            s1.update(label=f"❌ BigQuery error: {err}", state="error")
            st.info("Run `python3 scripts/bigquery_setup.py` once to create the dataset.")
            st.stop()
        s1.update(label=f"✅ Standard REST API complete — {std_time:.3f}s for {rows:,} rows", state="complete", expanded=False)

    # ── Step 2: Accelerated Storage API ────────────────────────────────────
    with st.status("⚡ Step 2 — Fetching via Accelerated BigQuery Storage Read API (Arrow)...", expanded=True) as s2:
        s2.update(label=f"✅ Storage Read API complete — {storage_time:.3f}s for {rows:,} rows", state="complete", expanded=False)

    # ── Metrics ─────────────────────────────────────────────────────────────
    speedup = round(std_time / storage_time, 1) if storage_time > 0 else 0
    st.markdown('<div class="section-label" style="margin-top:16px;">Benchmark Results</div>', unsafe_allow_html=True)
    bm1, bm2, bm3, bm4 = st.columns(4)
    bm1.metric("Rows Fetched",           f"{rows:,}",          help="Same result set from both queries")
    bm2.metric("Standard REST API",      f"{std_time:.3f}s",   help="Default BigQuery REST path")
    bm3.metric("Accelerated Storage API", f"{storage_time:.3f}s",
               delta=f"{speedup}x faster", delta_color="off",
               help="BigQuery Storage Read API — Arrow columnar, parallel streams")
    bm4.metric("Time Saved",             f"{round(std_time - storage_time, 3)}s",
               delta="per query", delta_color="off")

    # ── Speed comparison chart ───────────────────────────────────────────────
    st.plotly_chart(bq_fetch_chart(std_time, storage_time), use_container_width=True)

    st.markdown("""
<div class="rec-gpu">
⚡ <b>Why the Accelerated path is faster:</b><br><br>
The <b>BigQuery Storage Read API</b> streams data in parallel using Apache Arrow columnar format,
bypassing the standard REST serialization layer. For analytical workloads (aggregations, joins across
millions of rows) this eliminates the JSON encoding overhead — delivering the same result set
significantly faster, directly into a pandas DataFrame via zero-copy Arrow buffers.
</div>
""", unsafe_allow_html=True)

    # ── Full data tables ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:16px;">Live Data Preview</div>', unsafe_allow_html=True)
    with st.spinner("Loading full dataset preview..."):
        df_sample, df_agg, _, _, _ = fetch_bq_data()

    if df_sample is not None:
        bq_tab1, bq_tab2 = st.tabs(["📋 Top 100 Records by Risk Score", "📊 Risk Breakdown by Origin Port"])
        with bq_tab1:
            st.dataframe(df_sample, use_container_width=True, hide_index=True, height=260)
        with bq_tab2:
            risk_by_port = (
                df_agg[df_agg["status"] == "AT_RISK"]
                .groupby("origin_port")["shipments"].sum()
                .sort_values(ascending=False)
            )
            st.plotly_chart(bq_risk_chart(risk_by_port), use_container_width=True)

st.divider()

# ── AI Triage Results ──────────────────────────────────────────────────────────
if run_triage:
    st.markdown("## 🤖 AI Triage Results")

    tab_cpu, tab_gpu, tab_compare = st.tabs([
        "🐌 Standard Agent (CPU)",
        "⚡ Accelerated Agent (GPU + NIM)",
        "📊 Performance Comparison",
    ])

    with tab_cpu:
        with st.status("Running Standard Agent (CPU path)...", expanded=True) as s:
            result_cpu = workflow.invoke({"disruption_alert": ALERT_TEXT, "is_accelerated": False, "execution_logs": [], "disruption_type": "", "affected_hub": "", "affected_routes": []})
            for log in result_cpu.get("execution_logs", []):
                st.write(log)
            s.update(label="Standard Agent — Completed (Degraded Mode)", state="error", expanded=False)

        st.markdown('<div class="section-label">Agent Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rec-cpu">⚠️ {result_cpu.get("routing_plan", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-top:20px;">Performance Telemetry</div>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Data Join Latency", f"{result_cpu.get('db_latency', 0):.1f} sec")
        m2.metric("Throughput",        f"{result_cpu.get('throughput', 0):,} rows/s")
        m3.metric("Context Accuracy",  f"{result_cpu.get('accuracy', 0)}%",  delta="Data truncated", delta_color="inverse")
        m4.metric("Cost Exposure",     f"${result_cpu.get('cost_impact', 0):,}", delta="Unresolved",  delta_color="inverse")

    with tab_gpu:
        with st.status("Running Accelerated Agent (GPU + NIM)...", expanded=True) as s:
            result_gpu = workflow.invoke({"disruption_alert": ALERT_TEXT, "is_accelerated": True, "execution_logs": [], "disruption_type": "", "affected_hub": "", "affected_routes": []})
            for log in result_gpu.get("execution_logs", []):
                st.write(log)
            s.update(label="Accelerated Agent — Completed", state="complete", expanded=False)

        st.markdown('<div class="section-label">Agent Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rec-gpu">✅ {result_gpu.get("routing_plan", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-top:20px;">Performance Telemetry</div>', unsafe_allow_html=True)

        cpu_lat = result_cpu.get("db_latency", 184)
        gpu_lat = result_gpu.get("db_latency", 0.8)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Data Join Latency", f"{gpu_lat:.2f} sec",
                  delta=f"-{cpu_lat - gpu_lat:.1f}s vs CPU", delta_color="inverse")
        m2.metric("Throughput",        f"{result_gpu.get('throughput', 0):,} rows/s",
                  delta=f"+{result_gpu.get('throughput', 0) - result_cpu.get('throughput', 0):,}")
        m3.metric("Context Accuracy",  f"{result_gpu.get('accuracy', 0)}%",
                  delta=f"+{result_gpu.get('accuracy', 0) - result_cpu.get('accuracy', 0):.1f}%")
        m4.metric("Cost Saved",        f"${result_cpu.get('cost_impact', 0) - result_gpu.get('cost_impact', 0):,}",
                  delta="vs unresolved")

    with tab_compare:
        c1, c2 = st.columns(2)
        c1.plotly_chart(latency_chart(result_cpu.get("db_latency", 184), result_gpu.get("db_latency", 0.8)),  use_container_width=True)
        c2.plotly_chart(cost_chart(result_cpu.get("cost_impact", 145000), result_gpu.get("cost_impact", 12000)), use_container_width=True)

        c3, c4 = st.columns(2)
        c3.plotly_chart(accuracy_gauge(result_gpu.get("accuracy", 98), result_cpu.get("accuracy", 42)),        use_container_width=True)
        c4.plotly_chart(throughput_chart(result_cpu.get("throughput", 32000), result_gpu.get("throughput", 7000000)), use_container_width=True)

    # ── Human-in-the-Loop ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔐 Human Oversight — Authorize Routing Update")
    st.markdown(
        f'<div class="rec-gpu" style="margin-bottom:16px;">'
        f'<b>Pending Authorization:</b><br><br>{result_gpu.get("routing_plan", "")}</div>',
        unsafe_allow_html=True,
    )
    col_approve, col_reject, col_escalate, _ = st.columns([1.2, 1, 1.4, 3])
    if col_approve.button("✅ Approve & Execute", type="primary", use_container_width=True):
        st.success("Routing update dispatched to ERP. All affected carriers notified.")
        st.balloons()
    if col_reject.button("❌ Reject Plan", use_container_width=True):
        st.warning("Plan rejected. Agents standing by for re-analysis.")
    if col_escalate.button("🔺 Escalate to Manager", use_container_width=True):
        st.info("Incident escalated. Notification sent to supply chain director.")


