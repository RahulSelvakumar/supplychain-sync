import random
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


@st.cache_data(ttl=300)
def get_shipment_data() -> pd.DataFrame:
    random.seed(42)
    rows = [
        ("SG-001", "Singapore → Rotterdam",   "Container",    45200, "🔴 Port Strike"),
        ("SG-002", "Singapore → Los Angeles", "Bulk Carrier", 38700, "🔴 Port Strike"),
        ("HK-003", "Hong Kong → Hamburg",     "Container",    29100, "🟢 On Schedule"),
        ("JP-004", "Tokyo → Seattle",         "Container",    52400, "🟡 Minor Delay"),
        ("CN-005", "Shanghai → Felixstowe",   "Container",    61800, "🟢 On Schedule"),
        ("KR-006", "Busan → Long Beach",      "RoRo",         18900, "🟢 On Schedule"),
        ("MY-007", "Port Klang → Antwerp",    "Container",    34500, "🔴 Port Strike"),
        ("IN-008", "Mumbai → Dubai",          "Tanker",       27300, "🟢 On Schedule"),
    ]
    data = []
    for rid, route, vtype, units, status in rows:
        eta = datetime.now() + timedelta(days=random.randint(2, 18))
        data.append({
            "Route ID":      rid,
            "Route":         route,
            "Vessel Type":   vtype,
            "Units at Risk": f"{units:,}",
            "ETA":           eta.strftime("%d %b %Y"),
            "Status":        status,
        })
    return pd.DataFrame(data)
