import streamlit as st
import pandas as pd
from agents import workflow

st.set_page_config(page_title="SupplyChain Sync | NVIDIA + GCP", layout="wide")

st.markdown("""
    <style>
    .alert-banner { background-color: #ff4b4b; color: white; padding: 15px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

st.title("🌐 SupplyChain Sync: Autonomous Disruption Triage")
st.caption("Powered by Google Gemini 1.5 Pro, Vertex AI, NVIDIA NIM, and RAPIDS cuDF")
st.divider()

alert_text = "Port Strike Detected (Singapore Hub) - 5 Million Active Records at Risk"
st.markdown(f'<div class="alert-banner">🚨 CRITICAL ALERT: {alert_text}</div>', unsafe_allow_html=True)

if st.button("🚀 Initialize Multi-Agent Triage Protocol", type="primary", use_container_width=True):
    st.divider()
    col1, col_spacer, col2 = st.columns([1, 0.1, 1])
    
    # --- CPU EXECUTION (STANDARD AGENT) ---
    with col1:
        st.subheader("🐌 Standard Agent (Legacy CPU)")
        with st.status("Executing LangGraph (CPU path)...", expanded=True) as status_cpu:
            result_cpu = workflow.invoke({"disruption_alert": alert_text, "is_accelerated": False, "execution_logs": []})
            for log in result_cpu.get("execution_logs", []): st.write(log)
            status_cpu.update(label="Execution Complete (Degraded)", state="error", expanded=False)
            
        st.error("**Agent Recommendation:**")
        st.info(f"> {result_cpu.get('routing_plan', '⚠️ Error: Agent state lost.')}")
        
        # CPU Metrics
        st.markdown("### 📉 Telemetry & Business Impact")
        st.metric(label="⏱️ Data Join Latency", value=f"{result_cpu.get('db_latency', 0)} sec")
        st.metric(label="🧮 Data Throughput", value=f"{result_cpu.get('throughput', 0):,} rows/s")
        st.metric(label="🎯 Context Accuracy", value=f"{result_cpu.get('accuracy', 0)}%")
        st.metric(label="💸 Operational Cost Impact", value=f"-${result_cpu.get('cost_impact', 0):,}")

    # --- GPU EXECUTION (NVIDIA ACCELERATED AGENT) ---
    with col2:
        st.subheader("⚡ Accelerated Agent (NVIDIA cuDF + NIM)")
        with st.status("Executing LangGraph (GPU path)...", expanded=True) as status_gpu:
            result_gpu = workflow.invoke({"disruption_alert": alert_text, "is_accelerated": True, "execution_logs": []})
            for log in result_gpu.get("execution_logs", []): st.write(log)
            status_gpu.update(label="Execution Complete", state="complete", expanded=False)
            
        st.success("**Agent Recommendation (High-Precision):**")
        st.info(f"> {result_gpu.get('routing_plan', '⚠️ Error: Agent state lost.')}")
        
        # GPU Metrics with Deltas (Comparing GPU vs CPU)
        st.markdown("### 📈 Telemetry & Business Impact")
        st.metric(label="⏱️ Data Join Latency", value=f"{result_gpu.get('db_latency', 0)} sec", delta="-183.4 sec", delta_color="inverse")
        st.metric(label="🧮 Data Throughput", value=f"{result_gpu.get('throughput', 0):,} rows/s", delta="+6,222,856 rows/s")
        st.metric(label="🎯 Context Accuracy", value=f"{result_gpu.get('accuracy', 0)}%", delta="+57.3%")
        st.metric(label="💸 Operational Cost Impact", value=f"-${result_gpu.get('cost_impact', 0):,}", delta="+$133,000 Saved", delta_color="normal")

 # --- VISUAL GRAPH COMPARISON ---
    st.divider()
    st.subheader("📊 Performance vs. Cost Matrix")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**⏱️ Processing Latency (Lower is Better)**")
        latency_data = pd.DataFrame({
            "Architecture": ["Standard (CPU)", "Accelerated (GPU)"],
            "Seconds": [result_cpu.get('db_latency', 184.2), result_gpu.get('db_latency', 0.8)]
        }).set_index("Architecture")
        st.bar_chart(latency_data, color="#ff4b4b", height=250)
        
    with col_chart2:
        st.markdown("**💸 Operational Cost Impact (Lower is Better)**")
        cost_data = pd.DataFrame({
            "Architecture": ["Standard (CPU)", "Accelerated (GPU)"],
            "Cost ($)": [result_cpu.get('cost_impact', 145000), result_gpu.get('cost_impact', 12000)]
        }).set_index("Architecture")
        st.bar_chart(cost_data, color="#00d26a", height=250)

    # --- HUMAN IN THE LOOP ---
    st.divider()
    st.subheader("🔐 Human Oversight Gateway")
    col_app, col_rej, _ = st.columns([1, 1, 4])
    if col_app.button("✅ APPROVE & EXECUTE", type="primary"):
        st.toast('API Call sent to ERP! Routing Updated.', icon='🎉')
    if col_rej.button("❌ REJECT PLAN"):
        st.toast('Plan rejected. Agents standing by.', icon='🛑')