#!/usr/bin/env python3
"""
One-time setup: creates BigQuery dataset + shipments table with 500K synthetic rows.
All data generation runs server-side inside BigQuery (fast, no local compute needed).

Run once:
    gcloud auth application-default login
    python3 bigquery_setup.py
"""
from google.cloud import bigquery

PROJECT = "supplychain-sync-hackathon"
DATASET = "supply_chain"
TABLE   = "shipments"


def main():
    client = bigquery.Client(project=PROJECT)

    # ── Create dataset ────────────────────────────────────────────────────────
    ds_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    ds_ref.location = "US"
    client.create_dataset(ds_ref, exists_ok=True)
    print(f"✅ Dataset ready: {PROJECT}.{DATASET}")

    # ── Create table with 500K rows (generated entirely inside BigQuery) ──────
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT}.{DATASET}.{TABLE}` AS
    SELECT
      CONCAT('SHIP-', LPAD(CAST(id AS STRING), 7, '0')) AS shipment_id,

      CASE CAST(FLOOR(RAND() * 8) AS INT64)
        WHEN 0 THEN 'Singapore'  WHEN 1 THEN 'Port Klang'
        WHEN 2 THEN 'Shanghai'   WHEN 3 THEN 'Hong Kong'
        WHEN 4 THEN 'Tokyo'      WHEN 5 THEN 'Busan'
        WHEN 6 THEN 'Mumbai'     ELSE    'Shenzhen'
      END AS origin_port,

      CASE CAST(FLOOR(RAND() * 8) AS INT64)
        WHEN 0 THEN 'Rotterdam'   WHEN 1 THEN 'Los Angeles'
        WHEN 2 THEN 'Hamburg'     WHEN 3 THEN 'Felixstowe'
        WHEN 4 THEN 'Long Beach'  WHEN 5 THEN 'Antwerp'
        WHEN 6 THEN 'Dubai'       ELSE    'Seattle'
      END AS destination_port,

      CASE CAST(FLOOR(RAND() * 4) AS INT64)
        WHEN 0 THEN 'Container'  WHEN 1 THEN 'Bulk Carrier'
        WHEN 2 THEN 'Tanker'     ELSE    'RoRo'
      END AS vessel_type,

      CASE CAST(FLOOR(RAND() * 7) AS INT64)
        WHEN 0 THEN 'Electronics'   WHEN 1 THEN 'Automotive'
        WHEN 2 THEN 'Chemicals'     WHEN 3 THEN 'Consumer Goods'
        WHEN 4 THEN 'Raw Materials' WHEN 5 THEN 'Textiles'
        ELSE    'Machinery'
      END AS commodity,

      CAST(1000 + RAND() * 99000 AS INT64)         AS units,
      ROUND(5000.0 + RAND() * 495000.0, 2)          AS weight_kg,
      DATE_SUB(CURRENT_DATE(), INTERVAL CAST(RAND() * 90  AS INT64) DAY) AS departure_date,
      DATE_ADD(CURRENT_DATE(),  INTERVAL CAST(7 + RAND() * 21 AS INT64) DAY) AS eta_date,

      CASE
        WHEN RAND() < 0.12 THEN 'AT_RISK'
        WHEN RAND() < 0.25 THEN 'DELAYED'
        WHEN RAND() < 0.65 THEN 'IN_TRANSIT'
        ELSE 'ON_SCHEDULE'
      END AS status,

      ROUND(RAND(), 4)  AS route_risk_score,
      CONCAT('CARRIER-', CAST(CAST(RAND() * 20 AS INT64) + 1 AS STRING)) AS carrier_id,
      RAND() < 0.12     AS disruption_flag

    FROM UNNEST(GENERATE_ARRAY(1, 500000)) AS id
    """

    print("⏳ Generating 500,000 rows server-side in BigQuery...")
    job = client.query(sql)
    job.result()
    print(f"✅ Table ready: {PROJECT}.{DATASET}.{TABLE}")

    # ── Verify ────────────────────────────────────────────────────────────────
    rows = list(client.query(
        f"SELECT COUNT(*) as cnt, COUNTIF(status='AT_RISK') as at_risk "
        f"FROM `{PROJECT}.{DATASET}.{TABLE}`"
    ).result())[0]
    print(f"✅ {rows.cnt:,} total rows · {rows.at_risk:,} AT_RISK shipments")


if __name__ == "__main__":
    main()
