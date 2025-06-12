# satellite_tracker_mvp.py

"""
🚀 Real-Time Satellite Tracker (Stable)

Uses updated CelesTrak GP TLE endpoints, excludes HTML errors,
supports unlimited satellites, search, type filter, and clean UI.

Instructions:
    pip install streamlit pandas requests skyfield plotly
    # Optional: pip install flag
    streamlit run satellite_tracker_mvp.py
"""

import streamlit as st
import pandas as pd
import requests
from skyfield.api import EarthSatellite, load, wgs84
import plotly.graph_objects as go

# Fallback for flag
try:
    from flag import flag
except ImportError:
    flag = lambda country: ''

# TLE feed groups with the new GP PHP format
TLE_GROUPS = [
    "active", "stations", "science", "communications",
    "gps-ops", "resource", "weather"
]

@st.cache_data(ttl=3600)  # cache TLEs for 1 hour
def fetch_tle():
    """Fetch TLE lines from JSON-based CelesTrak GP endpoints."""
    all_tles = []
    for grp in TLE_GROUPS:
        url = f"https://celestrak.com/NORAD/elements/gp.php?GROUP={grp}&FORMAT=tle"
        resp = requests.get(url)
        lines = resp.text.strip().splitlines()
        # lines come in blocks of 3; ensure valid set
        for i in range(0, len(lines) - 2, 3):
            name, l1, l2 = lines[i], lines[i+1], lines[i+2]
            if l1.startswith("1 ") and l2.startswith("2 "):
                all_tles.append((name.strip(), l1.strip(), l2.strip()))
    return all_tles

def compute_positions(tle_list):
    """Propagate satellite positions and attach metadata."""
    ts = load.timescale()
    now = ts.now()
    rows = []
    for name, l1, l2 in tle_list:
        try:
            sat = EarthSatellite(l1, l2, name, ts)
            subpoint = wgs84.subpoint(sat.at(now))
            rows.append({
                "Name": name,
                "Latitude": subpoint.latitude.degrees,
                "Longitude": subpoint.longitude.degrees,
                "Altitude (km)": round(subpoint.elevation.km, 1),
                "TLE1": l1,
                "TLE2": l2,
                "Country": detect_country(name),
                "Type": detect_type(name)
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

def detect_country(name):
    n = name.upper()
    if any(k in n for k in ["USA", "NAVSTAR", "GPS"]): return "USA"
    if any(k in n for k in ["ISRO", "INDIA"]): return "India"
    if any(k in n for k in ["CHINA", "CZ-"]): return "China"
    if any(k in n for k in ["COSMOS", "RUSS"]): return "Russia"
    if any(k in n for k in ["ESA", "EUROPE"]): return "EU"
    if any(k in n for k in ["JAXA", "JAPAN"]): return "Japan"
    return "Unknown"

def detect_type(name):
    n = name.lower()
    if "gps" in n: return "GPS"
    if "weather" in n or "meteo" in n: return "Weather"
    if "comm" in n or "satcom" in n or "telecom" in n: return "Communications"
    if "mil" in n or "spy" in n or "nro" in n: return "Military"
    if "resourc" in n or "eo-" in n: return "Earth Observation"
    if "science" in n or "research" in n: return "Science"
    return "Unknown"

def draw_map(df, selected=None):
    fig = go.Figure(go.Scattergeo(
        lon=df["Longitude"], lat=df["Latitude"],
        text=df["Name"], mode="markers",
        marker=dict(size=5, color=[
            "green" if n == selected else "crimson"
            for n in df["Name"]
        ]),
        hoverinfo="text"
    ))
    fig.update_layout(
        geo=dict(
            showland=True, showcountries=True, showocean=True,
            landcolor="rgb(230,230,230)",
            oceancolor="rgb(170,200,250)",
            projection_type="orthographic"
        ),
        margin=dict(l=0, r=0, t=20, b=0), height=600
    )
    return fig

# --- Streamlit App ---

st.set_page_config("🚀 Satellite Tracker", layout="wide")
st.title("🚀 Real-Time Satellite Tracker")

with st.spinner("Loading TLE data…"):
    tles = fetch_tle()
    df = compute_positions(tles)

st.success(f"Satellites loaded: {len(df):,}")

# Filters
col1, col2 = st.columns(2)
search = col1.text_input("🔍 Search Name")
typ = col2.selectbox("📦 Filter Type", ["All"] + sorted(df["Type"].unique()))

if search:
    df = df[df["Name"].str.contains(search, case=False, na=False)]
if typ != "All":
    df = df[df["Type"] == typ]

# Map
st.plotly_chart(draw_map(df), use_container_width=True)

# Details
sel = st.selectbox("📌 Select Satellite", df["Name"].tolist())
if sel:
    info = df[df["Name"] == sel].iloc[0].to_dict()
    info["Flag"] = flag(info["Country"])
    st.json(info)

# Full table
with st.expander("📊 View All Satellites"):
    st.dataframe(df)

st.caption("Data via CelesTrak GP TLE feeds ● Skyfield propagation")
