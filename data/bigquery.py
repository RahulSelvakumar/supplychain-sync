import time
import streamlit as st

from config import GCP_PROJECT, BQ_FULL_TABLE

# Same query run twice so the comparison is apples-to-apples
_BENCHMARK_SQL = f"""
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

_SAMPLE_SQL = f"""
    SELECT shipment_id, origin_port, destination_port, vessel_type,
           commodity, units, status,
           ROUND(route_risk_score, 3) AS risk_score, eta_date
    FROM `{BQ_FULL_TABLE}`
    ORDER BY route_risk_score DESC
    LIMIT 100
"""

_AGG_SQL = f"""
    SELECT origin_port, status,
           COUNT(*)                        AS shipments,
           SUM(units)                      AS total_units,
           ROUND(AVG(route_risk_score), 3) AS avg_risk
    FROM `{BQ_FULL_TABLE}`
    GROUP BY 1, 2
    ORDER BY total_units DESC
"""


def benchmark_bq_fetch():
    """
    Runs the same aggregation query twice:
      1. Standard REST API  (no Storage client)
      2. Accelerated path   (BigQuery Storage Read API, Arrow columnar)
    Returns (std_time, storage_time, rows_fetched, error)
    """
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT)

        # — Standard REST API ─────────────────────────────────────────────────
        t0 = time.time()
        df_std = client.query(_BENCHMARK_SQL).to_dataframe()
        std_time = round(time.time() - t0, 3)

        # — Accelerated Storage Read API (Arrow) ──────────────────────────────
        t0 = time.time()
        df_acc = client.query(_BENCHMARK_SQL).to_dataframe(create_bqstorage_client=True)
        storage_time = round(time.time() - t0, 3)

        return std_time, storage_time, len(df_acc), None
    except Exception as e:
        return 0.0, 0.0, 0, str(e)


@st.cache_data(ttl=300)
def fetch_bq_data():
    """Full fetch: sample rows + aggregation for dashboard display."""
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=GCP_PROJECT)

        t0 = time.time()
        df_sample = client.query(_SAMPLE_SQL).to_dataframe()
        std_time = round(time.time() - t0, 2)

        t0 = time.time()
        df_agg = client.query(_AGG_SQL).to_dataframe(create_bqstorage_client=True)
        storage_time = round(time.time() - t0, 2)

        return df_sample, df_agg, std_time, storage_time, None
    except Exception as e:
        return None, None, 0.0, 0.0, str(e)

