import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
from datetime import datetime, timedelta
from agents import workflow

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupplyChain Sync | Command Center",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
div[data-testid="metric-container"] {
    background: #1e2130;
    border: 1px solid #2d3042;
    border-radius: 10px;
    padding: 14px 18px;
}
.alert-critical {
    background: linear-gradient(90deg, #ff4b4b18, #ff4b4b08);
    border-left: 4px solid #ff4b4b;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.alert-title { font-weight: 700; font-size: 1rem; color: #ff6b6b; }
.alert-body  { font-size: 0.83rem; margin-top: 4px; color: #cc9999; }
.rec-gpu {
    background: #0a1f12;
    border: 1px solid #00d26a44;
    border-radius: 10px;
    padding: 16px;
    font-size: 0.9rem;
    color: #ccffdd;
    line-height: 1.7;
    margin-top: 8px;
}
.rec-cpu {
    background: #1f0a0a;
    border: 1px solid #ff4b4b44;
    border-radius: 10px;
    padding: 16px;
    font-size: 0.9rem;
    color: #ffdddd;
    line-height: 1.7;
    margin-top: 8px;
}
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #556;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 12px 0 6px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid #2d3042;
}
</style>
""", unsafe_allow_html=True)

ALERT_TEXT = "Port Strike Detected (Singapore Hub) - 5 Million Active Records at Risk"

# ── Simulated Shipment Data ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_shipment_data():
    random.seed(42)
    rows = [
        ("SG-001", "Singapore → Rotterdam",   "Container",   45200, "🔴 Port Strike",  "CRITICAL"),
        ("SG-002", "Singapore → Los Angeles", "Bulk Carrier", 38700, "🔴 Port Strike",  "CRITICAL"),
        ("HK-003", "Hong Kong → Hamburg",     "Container",   29100, "🟢 On Schedule",  "ON TIME"),
        ("JP-004", "Tokyo → Seattle",         "Container",   52400, "🟡 Minor Delay",  "DELAYED"),
        ("CN-005", "Shanghai → Felixstowe",   "Container",   61800, "🟢 On Schedule",  "ON TIME"),
        ("KR-006", "Busan → Long Beach",      "RoRo",        18900, "🟢 On Schedule",  "ON TIME"),
        ("MY-007", "Port Klang → Antwerp",    "Container",   34500, "🔴 Port Strike",  "CRITICAL"),
        ("IN-008", "Mumbai → Dubai",          "Tanker",      27300, "🟢 On Schedule",  "ON TIME"),
    ]
    data = []
    for rid, route, vtype, units, status, _ in rows:
        eta = datetime.now() + timedelta(days=random.randint(2, 18))
        data.append({
            "Route ID":     rid,
            "Route":        route,
            "Vessel Type":  vtype,
            "Units at Risk": f"{units:,}",
            "ETA":          eta.strftime("%d %b %Y"),
            "Status":       status,
        })
    return pd.DataFrame(data)

# ── Sidebar ───────────────────────────────────────────────────────────────────
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

# ── Header ────────────────────────────────────────────────────────────────────
hdr, ts = st.columns([3, 1])
with hdr:
    st.markdown("## Supply Chain Command Center")
    st.caption("Real-time AI disruption triage · Google Vertex AI + NVIDIA NIM")
with ts:
    st.markdown(
        f"<div style='text-align:right;padding-top:10px;color:#8892b0;font-size:0.8rem;'>"
        f"Last updated<br><b style='color:#cdd;font-size:0.95rem;'>"
        f"{datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}</b></div>",
        unsafe_allow_html=True,
    )

# ── KPI Strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Active Routes",     "8",        delta="3 disrupted",      delta_color="inverse")
k2.metric("Units at Risk",     "5.25M",    delta="Singapore hub",    delta_color="inverse")
k3.metric("Cost Exposure",     "$145,000", delta="If unresolved",    delta_color="inverse")
k4.metric("AI Agents Online",  "4 / 4",   delta="All systems ready")

st.divider()

# ── Alert Banner ──────────────────────────────────────────────────────────────
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

# ── Active Shipments Table ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Active Shipment Routes</div>', unsafe_allow_html=True)
st.dataframe(get_shipment_data(), use_container_width=True, hide_index=True, height=290)

# ── Triage Results ────────────────────────────────────────────────────────────
if run_triage:
    st.divider()
    st.markdown("## 🤖 AI Triage Results")

    tab_cpu, tab_gpu, tab_compare = st.tabs([
        "🐌 Standard Agent (CPU)",
        "⚡ Accelerated Agent (GPU + NIM)",
        "📊 Performance Comparison",
    ])

    # ── CPU Tab ───────────────────────────────────────────────────────────────
    with tab_cpu:
        with st.status("Running Standard Agent (CPU path)...", expanded=True) as s:
            result_cpu = workflow.invoke({
                "disruption_alert": ALERT_TEXT,
                "is_accelerated": False,
                "execution_logs": [],
            })
            for log in result_cpu.get("execution_logs", []):
                st.write(log)
            s.update(label="Standard Agent — Completed (Degraded Mode)", state="error", expanded=False)

        st.markdown('<div class="section-label">Agent Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rec-cpu">⚠️ {result_cpu.get("routing_plan", "")}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:20px;">Performance Telemetry</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Data Join Latency",  f"{result_cpu.get('db_latency', 0):.1f} sec",   help="Time to process 5M+ rows on CPU")
        m2.metric("Throughput",         f"{result_cpu.get('throughput', 0):,} rows/s")
        m3.metric("Context Accuracy",   f"{result_cpu.get('accuracy', 0)}%",             delta="Data truncated", delta_color="inverse")
        m4.metric("Cost Exposure",      f"${result_cpu.get('cost_impact', 0):,}",        delta="Unresolved",     delta_color="inverse")

    # ── GPU Tab ───────────────────────────────────────────────────────────────
    with tab_gpu:
        with st.status("Running Accelerated Agent (GPU + NIM)...", expanded=True) as s:
            result_gpu = workflow.invoke({
                "disruption_alert": ALERT_TEXT,
                "is_accelerated": True,
                "execution_logs": [],
            })
            for log in result_gpu.get("execution_logs", []):
                st.write(log)
            s.update(label="Accelerated Agent — Completed", state="complete", expanded=False)

        st.markdown('<div class="section-label">Agent Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rec-gpu">✅ {result_gpu.get("routing_plan", "")}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:20px;">Performance Telemetry</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        cpu_lat = result_cpu.get("db_latency", 184)
        gpu_lat = result_gpu.get("db_latency", 0.8)
        m1.metric("Data Join Latency",  f"{gpu_lat:.2f} sec",
                  delta=f"-{cpu_lat - gpu_lat:.1f}s vs CPU",         delta_color="inverse")
        m2.metric("Throughput",         f"{result_gpu.get('throughput', 0):,} rows/s",
                  delta=f"+{result_gpu.get('throughput',0) - result_cpu.get('throughput',0):,}")
        m3.metric("Context Accuracy",   f"{result_gpu.get('accuracy', 0)}%",
                  delta=f"+{result_gpu.get('accuracy',0) - result_cpu.get('accuracy',0):.1f}%")
        m4.metric("Cost Saved",         f"${result_cpu.get('cost_impact', 0) - result_gpu.get('cost_impact', 0):,}",
                  delta="vs unresolved")

    # ── Comparison Tab ────────────────────────────────────────────────────────
    with tab_compare:
        PLOT_BG   = "#1e2130"
        FONT_COL  = "#c9d1d9"
        GRID_COL  = "#2d3042"
        CPU_COLOR = "#ff4b4b"
        GPU_COLOR = "#00d26a"

        c1, c2 = st.columns(2)

        with c1:
            fig = go.Figure()
            fig.add_bar(
                x=["Standard CPU", "Accelerated GPU"],
                y=[result_cpu.get("db_latency", 184), result_gpu.get("db_latency", 0.8)],
                marker_color=[CPU_COLOR, GPU_COLOR],
                text=[f"{result_cpu.get('db_latency', 184):.1f}s",
                      f"{result_gpu.get('db_latency', 0.8):.2f}s"],
                textposition="outside",
                width=0.4,
            )
            fig.update_layout(
                title=dict(text="⏱️ Data Join Latency — lower is better", font=dict(size=13)),
                yaxis=dict(title="Seconds", gridcolor=GRID_COL, color=FONT_COL),
                xaxis=dict(color=FONT_COL),
                paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                font=dict(color=FONT_COL), showlegend=False,
                margin=dict(t=45, b=10, l=10, r=10), height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = go.Figure()
            fig.add_bar(
                x=["Standard CPU", "Accelerated GPU"],
                y=[result_cpu.get("cost_impact", 145000), result_gpu.get("cost_impact", 12000)],
                marker_color=[CPU_COLOR, GPU_COLOR],
                text=[f"${result_cpu.get('cost_impact', 145000):,}",
                      f"${result_gpu.get('cost_impact', 12000):,}"],
                textposition="outside",
                width=0.4,
            )
            fig.update_layout(
                title=dict(text="💸 Operational Cost Impact — lower is better", font=dict(size=13)),
                yaxis=dict(title="USD ($)", gridcolor=GRID_COL, color=FONT_COL),
                xaxis=dict(color=FONT_COL),
                paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                font=dict(color=FONT_COL), showlegend=False,
                margin=dict(t=45, b=10, l=10, r=10), height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

        c3, c4 = st.columns(2)

        with c3:
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=result_gpu.get("accuracy", 98),
                delta={"reference": result_cpu.get("accuracy", 42), "valueformat": ".1f",
                       "increasing": {"color": GPU_COLOR}},
                title={"text": "🎯 GPU Accuracy vs CPU Baseline", "font": {"color": FONT_COL, "size": 13}},
                number={"suffix": "%", "font": {"color": FONT_COL}},
                gauge={
                    "axis":  {"range": [0, 100], "tickcolor": FONT_COL},
                    "bar":   {"color": GPU_COLOR},
                    "bgcolor": PLOT_BG,
                    "bordercolor": GRID_COL,
                    "steps": [
                        {"range": [0,  50], "color": "#3a1010"},
                        {"range": [50, 80], "color": "#2a2a10"},
                        {"range": [80,100], "color": "#0a2a15"},
                    ],
                    "threshold": {
                        "line": {"color": CPU_COLOR, "width": 3},
                        "thickness": 0.75,
                        "value": result_cpu.get("accuracy", 42),
                    },
                },
            ))
            fig.update_layout(
                paper_bgcolor=PLOT_BG, font=dict(color=FONT_COL),
                height=280, margin=dict(t=30, b=10, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with c4:
            tp_vals = [result_cpu.get("throughput", 32000), result_gpu.get("throughput", 7000000)]
            fig = go.Figure()
            fig.add_bar(
                x=["Standard CPU", "Accelerated GPU"],
                y=tp_vals,
                marker_color=[CPU_COLOR, GPU_COLOR],
                text=[f"{v:,}" for v in tp_vals],
                textposition="outside",
                width=0.4,
            )
            fig.update_layout(
                title=dict(text="🚀 Data Throughput — higher is better", font=dict(size=13)),
                yaxis=dict(title="Rows / second", gridcolor=GRID_COL, color=FONT_COL),
                xaxis=dict(color=FONT_COL),
                paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
                font=dict(color=FONT_COL), showlegend=False,
                margin=dict(t=45, b=10, l=10, r=10), height=280,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Human-in-the-Loop ─────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔐 Human Oversight — Authorize Routing Update")

    plan = result_gpu.get("routing_plan", "")
    st.markdown(f'<div class="rec-gpu" style="margin-bottom:16px;"><b>Pending Authorization:</b><br><br>{plan}</div>',
                unsafe_allow_html=True)

    col_approve, col_reject, col_escalate, _ = st.columns([1.2, 1, 1.4, 3])

    if col_approve.button("✅ Approve & Execute", type="primary", use_container_width=True):
        st.success("Routing update dispatched to ERP. All affected carriers notified.")
        st.balloons()
    if col_reject.button("❌ Reject Plan", use_container_width=True):
        st.warning("Plan rejected. Agents standing by for re-analysis.")
    if col_escalate.button("🔺 Escalate to Manager", use_container_width=True):
        st.info("Incident escalated. Notification sent to supply chain director.")