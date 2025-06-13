import streamlit as st
import pandas as pd
import requests
from skyfield.api import EarthSatellite, load, wgs84
import plotly.graph_objects as go

# --------------
# Configurations
# --------------
st.set_page_config("🌌 Space Dashboard", layout="wide")

# --------------
# Helpers
# --------------
TLE_GROUPS = [
    "active", "stations", "science", "communications",
    "gps-ops", "resource", "weather"
]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tle():
    all_tles = []
    for grp in TLE_GROUPS:
        url = f"https://celestrak.com/NORAD/elements/gp.php?GROUP={grp}&FORMAT=tle"
        try:
            resp = requests.get(url, timeout=5)
            lines = resp.text.strip().splitlines()
            for i in range(0, len(lines) - 2, 3):
                name, l1, l2 = lines[i], lines[i+1], lines[i+2]
                if l1.startswith("1 ") and l2.startswith("2 "):
                    all_tles.append((name.strip(), l1.strip(), l2.strip()))
        except requests.exceptions.RequestException:
            continue
    return all_tles

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_planetary_data():
    url = "https://api.le-systeme-solaire.net/rest/bodies/"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json().get("bodies", [])
    except requests.exceptions.RequestException:
        return []

def compute_sat_positions(tle_list):
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
                "TLE2": l2
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

def draw_satellite_map(df, selected=None):
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
        geo=dict(showland=True, showcountries=True, showocean=True,
                 landcolor="rgb(230,230,230)", oceancolor="rgb(170,200,250)",
                 projection_type="orthographic"),
        margin=dict(l=0, r=0, t=20, b=0), height=600
    )
    return fig

def draw_planetary_table(bodies):
    df = pd.DataFrame([{
        "Name": b.get("englishName"),
        "Type": b.get("bodyType", "Unknown"),
        "Mass (kg)": (
            b["mass"]["massValue"] * (10 ** b["mass"]["massExponent"])
            if b.get("mass") else None
        ),
        "Gravity (m/s²)": b.get("gravity"),
        "Radius (km)": b.get("meanRadius"),
        "Orbital Period (days)": b.get("sideralOrbit")
    } for b in bodies if b.get("englishName")])
    return df

# --------------
# App Layout
# --------------
tabs = st.tabs(["🛰 Satellites", "🪐 Solar System"])

# --- Satellite Tab ---
with tabs[0]:
    st.title("🛰 Real-Time Satellite Tracker")
    with st.spinner("Fetching TLE data..."):
        tles = fetch_tle()
        df_sats = compute_sat_positions(tles)
    st.success(f"Loaded {len(df_sats)} satellites")

    col1, col2 = st.columns(2)
    search = col1.text_input("🔍 Search by Name")
    if search:
        df_sats = df_sats[df_sats["Name"].str.contains(search, case=False)]

    st.plotly_chart(draw_satellite_map(df_sats), use_container_width=True)

    selected = st.selectbox("📌 Select Satellite", df_sats["Name"])
    st.json(df_sats[df_sats["Name"] == selected].iloc[0].to_dict())

    with st.expander("📊 All Satellites"):
        st.dataframe(df_sats)

# --- Solar System Tab ---
with tabs[1]:
    st.title("🪐 Solar System Explorer")
    with st.spinner("Loading planetary data..."):
        bodies = fetch_planetary_data()
    df_planets = draw_planetary_table(bodies)

    types = ["All"] + sorted(df_planets["Type"].dropna().unique())
    typ_filter = st.selectbox("🔭 Filter by Type", types)
    if typ_filter != "All":
        df_planets = df_planets[df_planets["Type"] == typ_filter]

    sel_planet = st.selectbox("🌍 Select a Body", df_planets["Name"].tolist())
    sel_data = next((b for b in bodies if b.get("englishName") == sel_planet), {})
    st.subheader(f"🧬 {sel_planet} — Key Details")
    st.json(sel_data)

    with st.expander("📊 Planetary Data Table"):
        st.dataframe(df_planets)

st.caption("Data via CelesTrak + le-systeme-solaire.net ")
