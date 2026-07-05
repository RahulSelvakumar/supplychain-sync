import plotly.graph_objects as go

_BG   = "#1e2130"
_FONT = "#c9d1d9"
_GRID = "#2d3042"
_RED  = "#ff4b4b"
_GRN  = "#00d26a"

_BASE_LAYOUT = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=dict(color=_FONT),
    showlegend=False,
    margin=dict(t=45, b=10, l=10, r=10),
)


def latency_chart(cpu_val: float, gpu_val: float) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=["Standard CPU", "Accelerated GPU"],
        y=[cpu_val, gpu_val],
        marker_color=[_RED, _GRN],
        text=[f"{cpu_val:.1f}s", f"{gpu_val:.2f}s"],
        textposition="outside",
        width=0.4,
    )
    fig.update_layout(
        title=dict(text="⏱️ Data Join Latency — lower is better", font=dict(size=13)),
        yaxis=dict(title="Seconds", gridcolor=_GRID, color=_FONT),
        xaxis=dict(color=_FONT),
        height=300,
        **_BASE_LAYOUT,
    )
    return fig


def cost_chart(cpu_val: int, gpu_val: int) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=["Standard CPU", "Accelerated GPU"],
        y=[cpu_val, gpu_val],
        marker_color=[_RED, _GRN],
        text=[f"${cpu_val:,}", f"${gpu_val:,}"],
        textposition="outside",
        width=0.4,
    )
    fig.update_layout(
        title=dict(text="💸 Operational Cost Impact — lower is better", font=dict(size=13)),
        yaxis=dict(title="USD ($)", gridcolor=_GRID, color=_FONT),
        xaxis=dict(color=_FONT),
        height=300,
        **_BASE_LAYOUT,
    )
    return fig


def accuracy_gauge(gpu_accuracy: float, cpu_accuracy: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gpu_accuracy,
        delta={"reference": cpu_accuracy, "valueformat": ".1f",
               "increasing": {"color": _GRN}},
        title={"text": "🎯 GPU Accuracy vs CPU Baseline", "font": {"color": _FONT, "size": 13}},
        number={"suffix": "%", "font": {"color": _FONT}},
        gauge={
            "axis":  {"range": [0, 100], "tickcolor": _FONT},
            "bar":   {"color": _GRN},
            "bgcolor": _BG,
            "bordercolor": _GRID,
            "steps": [
                {"range": [0,  50], "color": "#3a1010"},
                {"range": [50, 80], "color": "#2a2a10"},
                {"range": [80, 100], "color": "#0a2a15"},
            ],
            "threshold": {
                "line": {"color": _RED, "width": 3},
                "thickness": 0.75,
                "value": cpu_accuracy,
            },
        },
    ))
    fig.update_layout(
        height=280,
        paper_bgcolor=_BG,
        font=dict(color=_FONT),
        margin=dict(t=30, b=10, l=20, r=20),
    )
    return fig


def throughput_chart(cpu_val: int, gpu_val: int) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=["Standard CPU", "Accelerated GPU"],
        y=[cpu_val, gpu_val],
        marker_color=[_RED, _GRN],
        text=[f"{cpu_val:,}", f"{gpu_val:,}"],
        textposition="outside",
        width=0.4,
    )
    fig.update_layout(
        title=dict(text="🚀 Data Throughput — higher is better", font=dict(size=13)),
        yaxis=dict(title="Rows / second", gridcolor=_GRID, color=_FONT),
        xaxis=dict(color=_FONT),
        height=280,
        **_BASE_LAYOUT,
    )
    return fig


def bq_fetch_chart(std_time: float, storage_time: float) -> go.Figure:
    speedup = round(std_time / storage_time, 1) if storage_time > 0 else 1
    fig = go.Figure()
    fig.add_bar(
        x=["Standard REST API", "Accelerated Storage API"],
        y=[std_time, storage_time],
        marker_color=[_RED, _GRN],
        text=[f"{std_time:.3f}s", f"{storage_time:.3f}s  ({speedup}x faster)"],
        textposition="outside",
        width=0.4,
    )
    fig.update_layout(
        title=dict(text=f"⚡ Same Query · Storage API is {speedup}x faster — lower is better", font=dict(size=13)),
        yaxis=dict(title="Seconds", gridcolor=_GRID, color=_FONT),
        xaxis=dict(color=_FONT),
        height=300,
        **_BASE_LAYOUT,
    )
    return fig


def bq_risk_chart(risk_by_port) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(
        x=risk_by_port.index.tolist(),
        y=risk_by_port.values.tolist(),
        marker_color=_RED,
        text=risk_by_port.values.tolist(),
        textposition="outside",
        width=0.5,
    )
    fig.update_layout(
        title=dict(text="AT_RISK Shipments by Origin Port (live from BigQuery)", font=dict(size=13)),
        yaxis=dict(title="Shipment Count", gridcolor=_GRID, color=_FONT),
        xaxis=dict(color=_FONT),
        height=320,
        **_BASE_LAYOUT,
    )
    return fig
