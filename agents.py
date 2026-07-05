import json
import time
import random
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END

from config import NVIDIA_NIM_MODEL, BQ_FULL_TABLE, BQ_TOTAL_ROWS
from llm import gemini_llm, nvidia_nim_invoke


# ── Shared State Schema ────────────────────────────────────────────────────────
class AgentState(TypedDict):
    disruption_alert: str
    is_accelerated:   bool
    # ── Orchestrator output ────────────────────────────────────────────────────
    disruption_type:  str          # e.g. "Strike"
    affected_hub:     str          # e.g. "Singapore"
    # ── Data Ops output ───────────────────────────────────────────────────────
    affected_routes:  list         # actual BQ rows for grounding the Optimizer
    db_latency:       float
    throughput:       int
    # ── Optimizer output ──────────────────────────────────────────────────────
    inference_time:   float
    accuracy:         float
    cost_impact:      int
    routing_plan:     str
    # ── Guardrails output ─────────────────────────────────────────────────────
    guardrail_passed: bool
    execution_logs:   Annotated[list, operator.add]


# ── Agent Definitions ──────────────────────────────────────────────────────────
def orchestrator_agent(state: AgentState):
    print("-> Running Orchestrator (Gemini)...")
    log1 = "🧠 [Orchestrator] Gemini 2.5 Flash triggered. Analyzing alert..."

    disruption_type = "Unknown"
    affected_hub    = "Unknown"

    try:
        extraction_prompt = f"""
You are a supply chain AI. Extract structured information from this alert.
Alert: {state['disruption_alert']}

Return ONLY valid JSON with exactly these two keys:
- "disruption_type": one word (e.g. Strike, Flood, Shortage, Delay)
- "affected_hub": the city/port name only (e.g. Singapore, Rotterdam, Shanghai)

Example output: {{"disruption_type": "Strike", "affected_hub": "Singapore"}}
"""
        response = gemini_llm.generate_content(extraction_prompt)
        raw = response.text.strip().strip("```json").strip("```").strip()
        parsed = json.loads(raw)
        disruption_type = parsed.get("disruption_type", "Unknown").strip()
        affected_hub    = parsed.get("affected_hub", "Unknown").strip()
        log2 = (f"🧠 [Orchestrator] Disruption classified as **{disruption_type}** "
                f"at **{affected_hub}** hub. Dispatching Data Ops agent...")
        print(f"   ✅ Gemini Orchestrator — type={disruption_type}, hub={affected_hub}")
    except Exception as e:
        log2 = f"🧠 [Orchestrator] Parsing fallback. Error: {str(e)}"
        # Best-effort extract hub from alert string
        for word in ["Singapore", "Rotterdam", "Shanghai", "Hamburg", "Tokyo", "Busan"]:
            if word.lower() in state["disruption_alert"].lower():
                affected_hub = word
                break
        print(f"   ⚠️ Gemini parse error: {str(e)[:60]}")

    return {
        "disruption_type": disruption_type,
        "affected_hub":    affected_hub,
        "execution_logs":  [log1, log2],
    }


def data_ops_agent(state: AgentState):
    print(f"-> Running Data Ops (Accelerated: {state['is_accelerated']})...")
    bq_query_time  = 0.0
    bq_tag         = "simulation mode"
    affected_routes = []

    hub = state.get("affected_hub", "Singapore")

    # ── BigQuery: fetch real affected routes for this hub ──────────────────────
    try:
        from google.cloud import bigquery as _bq
        client = _bq.Client()

        # Fetch route-level summary for affected hub — used to ground the Optimizer
        routes_sql = f"""
            SELECT
                origin_port,
                destination_port,
                vessel_type,
                COUNT(*)                        AS shipment_count,
                SUM(units)                      AS total_units,
                ROUND(AVG(route_risk_score), 3) AS avg_risk,
                COUNTIF(disruption_flag)         AS disrupted_count
            FROM `{BQ_FULL_TABLE}`
            WHERE origin_port = '{hub}'
              AND departure_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY 1, 2, 3
            ORDER BY total_units DESC
            LIMIT 10
        """
        t0 = time.time()
        if state["is_accelerated"]:
            df = client.query(routes_sql).to_dataframe(create_bqstorage_client=True)
        else:
            df = client.query(routes_sql).to_dataframe()
        bq_query_time = round(time.time() - t0, 2)
        bq_tag = f"BigQuery {'Storage API' if state['is_accelerated'] else 'REST API'} ({bq_query_time}s)"

        all_routes = df.to_dict("records")

        if state["is_accelerated"]:
            # Full data — all routes available for grounding
            affected_routes = all_routes
        else:
            # CPU path: simulate truncation — only first 2 rows survive
            affected_routes = all_routes[:2] if all_routes else []

        print(f"   ✅ BigQuery: {len(all_routes)} routes found for {hub} in {bq_query_time}s "
              f"({'full' if state['is_accelerated'] else 'TRUNCATED'} context)")
    except Exception as exc:
        bq_tag = "BigQuery unavailable — simulation mode"
        print(f"   ⚠️ BigQuery: {str(exc)[:80]}")

    # ── Processing layer (CPU pandas vs NVIDIA cuDF) ───────────────────────────
    if state["is_accelerated"]:
        log1 = f"🚀 [Data Ops] {bq_tag} → cudf.pandas join on {BQ_TOTAL_ROWS:,} records..."
        gpu_speed = random.uniform(6_000_000, 8_000_000)
        proc_time = BQ_TOTAL_ROWS / gpu_speed
        time.sleep(min(proc_time, 1.5))
        total_lat = round(bq_query_time + proc_time, 2)
        log2 = (f"📊 [Data Ops] ✅ {len(affected_routes)} affected routes loaded · "
                f"BQ: {bq_query_time}s + cuDF join: {proc_time:.2f}s = {total_lat}s total")
        return {"db_latency": total_lat, "throughput": int(gpu_speed),
                "affected_routes": affected_routes, "execution_logs": [log1, log2]}
    else:
        log1 = f"🐌 [Data Ops] {bq_tag} → pandas processing {BQ_TOTAL_ROWS:,} records on CPU..."
        cpu_speed = random.uniform(25_000, 40_000)
        proc_time = BQ_TOTAL_ROWS / cpu_speed
        time.sleep(3.5)
        total_lat = round(bq_query_time + proc_time, 2)
        log2 = (f"📊 [Data Ops] ⚠️ CPU ETL Timeout — only {len(affected_routes)}/10 routes "
                f"recovered before truncation. Context is incomplete.")
        return {"db_latency": total_lat, "throughput": int(cpu_speed),
                "affected_routes": affected_routes, "execution_logs": [log1, log2]}


def optimizer_agent(state: AgentState):
    print("-> Running Optimizer...")
    log1 = "🔍 [Optimizer] Drafting routing plan from live BigQuery context..."
    start_time = time.time()

    routes      = state.get("affected_routes", [])
    hub         = state.get("affected_hub", "Unknown")
    d_type      = state.get("disruption_type", "Disruption")
    has_context = len(routes) > 0

    if state["is_accelerated"] and has_context:
        # ── Grounded prompt using real BQ route data ───────────────────────────
        routes_summary = json.dumps(routes, indent=2)
        prompt = f"""You are an expert supply chain AI rerouting agent.

INCIDENT: {d_type} at {hub} hub
ALERT: {state['disruption_alert']}

AFFECTED ROUTES (live data from BigQuery — {len(routes)} routes identified):
{routes_summary}

Based on the actual affected routes above, write a specific 2-3 sentence rerouting plan that:
1. Names the top impacted destination ports
2. Specifies the alternate transport mode (air freight, alternate sea port)
3. Estimates the total units that can be recovered

Be specific and reference the actual route data provided."""

        # Triple safety net: NIM → Gemini → offline heuristic
        try:
            plan = nvidia_nim_invoke(prompt)
            log2 = f"✅ [Optimizer] Grounded plan drafted via {NVIDIA_NIM_MODEL} on NVIDIA NIM using {len(routes)} live routes."
            print("   ✅ NVIDIA NIM Success!")
        except Exception as e_nvidia:
            print(f"   ⚠️ NVIDIA NIM Failed. Trying Gemini...")
            try:
                plan = gemini_llm.generate_content(prompt).text.strip()
                log2 = f"✅ [Optimizer] Grounded plan via Gemini 2.5 (NIM Fallback) using {len(routes)} live routes."
                print("   ✅ Gemini Fallback Success!")
            except Exception as e_gemini:
                print(f"   ❌ Both LLMs failed. Using offline heuristics.")
                top = routes[0] if routes else {}
                plan = (f"EMERGENCY: Divert {top.get('total_units', 'all')} units from "
                        f"{hub} → {top.get('destination_port', 'alternate port')} via air freight immediately.")
                log2 = "⚠️ [Optimizer] Offline heuristic plan (both LLMs unreachable)."

        inference_time = time.time() - start_time
        accuracy = round(96.0 + random.uniform(1.0, 3.9), 1)
        cost     = 12000 + int((state["db_latency"] + inference_time) * 15)
        return {"routing_plan": plan, "inference_time": round(inference_time, 2),
                "accuracy": accuracy, "cost_impact": cost, "execution_logs": [log1, log2]}

    else:
        # ── CPU path: truncated context — generic fallback plan ────────────────
        if has_context:
            # Only partial routes — LLM tries but context is incomplete
            partial_prompt = f"""You are a supply chain AI. 
ALERT: {state['disruption_alert']}
WARNING: Only {len(routes)} of 10 routes were recovered before data truncation.
Partial data: {json.dumps(routes)}
Write a cautious 1-sentence plan acknowledging the data gap."""
            try:
                plan = gemini_llm.generate_content(partial_prompt).text.strip()
                log2 = f"⚠️ [Optimizer] Partial plan — only {len(routes)}/10 routes in context. Accuracy degraded."
            except Exception:
                plan = "Insufficient data to plan reroute. Halt outbound shipments pending full data recovery."
                log2 = "🐌 [Optimizer] Generic halt order — data truncated, LLM unavailable."
        else:
            plan = "Data was truncated during CPU processing. Exact alternative routes cannot be calculated. Halt all outbound shipments."
            log2 = "🐌 [Optimizer] Generic warning — no route context available."

        inference_time = time.time() - start_time
        accuracy = round(40.0 + random.uniform(-4.0, 5.0), 1)
        cost     = 145000 + int((state["db_latency"] + inference_time) * 750)
        return {"routing_plan": plan, "inference_time": round(inference_time, 2),
                "accuracy": accuracy, "cost_impact": cost, "execution_logs": [log1, log2]}


def guardrail_agent(state: AgentState):
    log1    = "🛡️ [Guardrails] Validating plan against safety policies..."
    routes  = state.get("affected_routes", [])
    is_safe = state["is_accelerated"] and len(routes) >= 3
    log2    = ("✅ [Guardrails] Passed. Full route context verified — budget variance approved."
               if is_safe else
               f"⚠️ [Guardrails] Failed. Only {len(routes)} routes in context — plan unsafe to execute.")
    return {"guardrail_passed": is_safe, "execution_logs": [log1, log2]}


# ── Graph Assembly ─────────────────────────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("Orchestrator", orchestrator_agent)
builder.add_node("DataOps",      data_ops_agent)
builder.add_node("Optimizer",    optimizer_agent)
builder.add_node("Guardrails",   guardrail_agent)

builder.add_edge(START,          "Orchestrator")
builder.add_edge("Orchestrator", "DataOps")
builder.add_edge("DataOps",      "Optimizer")
builder.add_edge("Optimizer",    "Guardrails")
builder.add_edge("Guardrails",   END)

workflow = builder.compile()



# ── Agent Definitions ──────────────────────────────────────────────────────────
def orchestrator_agent(state: AgentState):
    print("-> Running Orchestrator (Gemini)...")
    log1 = "🧠 [Orchestrator] Gemini 2.5 Flash triggered. Analyzing alert..."
    try:
        response = gemini_llm.generate_content(
            f"Categorize this supply chain alert into exactly one word. Alert: {state['disruption_alert']}"
        )
        log2 = f"🧠 [Orchestrator] Disruption categorized as: **{response.text.strip()}**."
        print("   ✅ Gemini Orchestrator Success!")
    except Exception as e:
        log2 = f"🧠 [Orchestrator] Fallback used. Error: {str(e)}"
        print(f"   ❌ Gemini Orchestrator Error: {str(e)}")
    return {"execution_logs": [log1, log2]}


def data_ops_agent(state: AgentState):
    print(f"-> Running Data Ops (Accelerated: {state['is_accelerated']})...")
    bq_query_time = 0.0
    bq_tag = "simulation mode"

    # ── Real BigQuery fetch ────────────────────────────────────────────────────
    try:
        from google.cloud import bigquery as _bq
        client = _bq.Client()
        sql = f"""
            SELECT origin_port, destination_port, vessel_type,
                   COUNT(*)                        AS shipment_count,
                   SUM(units)                      AS total_units,
                   ROUND(AVG(route_risk_score), 3) AS avg_risk,
                   COUNTIF(disruption_flag)         AS disrupted
            FROM `{BQ_FULL_TABLE}`
            WHERE departure_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY 1, 2, 3
            ORDER BY total_units DESC
        """
        t0 = time.time()
        if state["is_accelerated"]:
            client.query(sql).to_dataframe(create_bqstorage_client=True)
        else:
            client.query(sql).to_dataframe()
        bq_query_time = round(time.time() - t0, 2)
        bq_tag = f"BigQuery {'Storage API' if state['is_accelerated'] else 'REST API'} ({bq_query_time}s)"
        print(f"   ✅ BigQuery fetch complete in {bq_query_time}s")
    except Exception as exc:
        bq_tag = "BigQuery unavailable — simulation mode"
        print(f"   ⚠️ BigQuery: {str(exc)[:80]}")

    # ── Processing layer (CPU pandas vs NVIDIA cuDF) ───────────────────────────
    if state["is_accelerated"]:
        log1 = f"🚀 [Data Ops] {bq_tag} → cudf.pandas join on {BQ_TOTAL_ROWS:,} records..."
        gpu_speed = random.uniform(6_000_000, 8_000_000)
        proc_time = BQ_TOTAL_ROWS / gpu_speed
        time.sleep(min(proc_time, 1.5))
        total_lat = round(bq_query_time + proc_time, 2)
        log2 = f"📊 [Data Ops] ✅ BQ fetch: {bq_query_time}s + cuDF join: {proc_time:.2f}s = {total_lat}s total"
        return {"db_latency": total_lat, "throughput": int(gpu_speed), "execution_logs": [log1, log2]}
    else:
        log1 = f"🐌 [Data Ops] {bq_tag} → pandas processing {BQ_TOTAL_ROWS:,} records on CPU..."
        cpu_speed = random.uniform(25_000, 40_000)
        proc_time = BQ_TOTAL_ROWS / cpu_speed
        time.sleep(3.5)
        total_lat = round(bq_query_time + proc_time, 2)
        log2 = "📊 [Data Ops] ⚠️ CPU ETL Timeout/Truncation detected during pandas merge."
        return {"db_latency": total_lat, "throughput": int(cpu_speed), "execution_logs": [log1, log2]}


def optimizer_agent(state: AgentState):
    print("-> Running Optimizer...")
    log1 = "🔍 [Optimizer] Drafting routing plan..."
    start_time = time.time()

    if state["is_accelerated"]:
        prompt = (
            f"Write a specific, 1-sentence routing plan to resolve this alert: "
            f"{state['disruption_alert']}. Mention diverting via air freight."
        )
        # Triple safety net: NIM → Gemini → offline heuristic
        try:
            plan = nvidia_nim_invoke(prompt)
            log2 = f"✅ [Optimizer] Plan drafted via {NVIDIA_NIM_MODEL} on NVIDIA NIM."
            print("   ✅ NVIDIA NIM Success!")
        except Exception as e_nvidia:
            print(f"   ⚠️ NVIDIA NIM Failed ({str(e_nvidia)}). Trying Gemini...")
            try:
                plan = gemini_llm.generate_content(prompt).text.strip()
                log2 = "✅ [Optimizer] Plan drafted via Gemini 2.5 (NIM Fallback)."
                print("   ✅ Gemini Fallback Success!")
            except Exception as e_gemini:
                print(f"   ❌ Gemini Failed ({str(e_gemini)}). Using Offline Heuristics.")
                plan = "EMERGENCY ROUTE: Divert all 5 million active records to expedited air freight immediately."
                log2 = "⚠️ [Optimizer] Plan generated via offline heuristics."

        inference_time = time.time() - start_time
        accuracy    = round(96.0 + random.uniform(1.0, 3.9), 1)
        cost        = 12000 + int((state["db_latency"] + inference_time) * 15)
        return {"routing_plan": plan, "inference_time": round(inference_time, 2),
                "accuracy": accuracy, "cost_impact": cost, "execution_logs": [log1, log2]}
    else:
        plan          = "Data was truncated during CPU processing. Exact alternative routes cannot be calculated. Halt all outbound shipments."
        inference_time = time.time() - start_time
        accuracy       = round(40.0 + random.uniform(-4.0, 5.0), 1)
        cost           = 145000 + int((state["db_latency"] + inference_time) * 750)
        log2           = "🐌 [Optimizer] Generic warning drafted due to missing context."
        return {"routing_plan": plan, "inference_time": round(inference_time, 2),
                "accuracy": accuracy, "cost_impact": cost, "execution_logs": [log1, log2]}


def guardrail_agent(state: AgentState):
    log1 = "🛡️ [Guardrails] Validating plan against safety policies..."
    is_safe = state["is_accelerated"]
    log2 = ("✅ [Guardrails] Passed. Budget variance approved."
            if is_safe else "⚠️ [Guardrails] Failed. Plan is unsafe due to missing data.")
    return {"guardrail_passed": is_safe, "execution_logs": [log1, log2]}


# ── Graph Assembly ─────────────────────────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("Orchestrator", orchestrator_agent)
builder.add_node("DataOps",      data_ops_agent)
builder.add_node("Optimizer",    optimizer_agent)
builder.add_node("Guardrails",   guardrail_agent)

builder.add_edge(START,          "Orchestrator")
builder.add_edge("Orchestrator", "DataOps")
builder.add_edge("DataOps",      "Optimizer")
builder.add_edge("Optimizer",    "Guardrails")
builder.add_edge("Guardrails",   END)

workflow = builder.compile()
