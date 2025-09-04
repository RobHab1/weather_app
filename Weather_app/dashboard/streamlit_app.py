import os
import pandas as pd
import requests
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Väderdashboard", page_icon="☀️", layout="wide")

# Minimal styling
st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
div[data-testid="stMetricValue"] {font-size: 28px;}
div[data-testid="stMetricDelta"] {font-size: 14px;}
</style>
""", unsafe_allow_html=True)

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
engine = create_engine('sqlite:///db.sqlite')

@st.cache_data(ttl=600)
def load_data(city: str) -> pd.DataFrame:
    q = f"select * from weather_obs where city = '{city}' order by ts"
    df = pd.read_sql(q, engine)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df

def fetch_backend(city: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}/weather/forecast", params={"city": city}, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_reco(city: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}/recommendations/run", params={"city": city}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_ice(city: str) -> dict:
    try:
        r = requests.get(f"{API_BASE}/alerts/ice", params={"city": city}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

st.title("Väderdashboard")

with st.sidebar:
    city = st.text_input("Stad", os.getenv("DEFAULT_CITY", "Stockholm"))
    col_a, col_b = st.columns(2)
    if col_a.button("Uppdatera prognos"):
        res = fetch_backend(city)
        st.toast(f"Hämtat: {res}", icon="✅" if "saved_points" in res else "⚠️")
        load_data.clear()  # rensa cache

df = load_data(city)

if df.empty:
    st.warning("Ingen data ännu. Kör Uppdatera prognos eller anropa API:t.")
    st.stop()

# Filter period
date_min = df["ts"].min().date()
date_max = df["ts"].max().date()
start_date, end_date = st.slider("Period", min_value=date_min, max_value=date_max, value=(date_min, date_max), format="YYYY-MM-DD")
mask = (df["ts"].dt.date >= start_date) & (df["ts"].dt.date <= end_date)
df = df.loc[mask].reset_index(drop=True)

# KPI-rad
col1, col2, col3, col4 = st.columns(4)
col1.metric("Mätpunkter", len(df))
col2.metric("Medeltemp °C", f"{df['temp_c'].mean():.1f}")
col3.metric("Max vind m/s", f"{df['wind_ms'].max():.1f}")
col4.metric("Andel torra %", f"{(df['precip_mm'].eq(0).mean()*100):.0f}")

tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Temperatur", "Vind", "Nederbörd"])

with tab1:
    reco = get_reco(city)
    ice = get_ice(city)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Bästa tider för träning")
        slots = reco.get("best_slots", [])
        if slots:
            st.write("\n".join(f"• {s}" for s in slots))
        else:
            st.info("Inga förslag i perioden.")
    with c2:
        st.subheader("Halkrisk")
        risk = ice.get("risk_slots", [])
        if risk:
            st.write("\n".join(f"• {s}" for s in risk))
        else:
            st.success("Ingen risk i perioden.")

with tab2:
    fig = px.line(df, x="ts", y="temp_c", labels={"ts": "Tid", "temp_c": "Temp (°C)"})
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.line(df, x="ts", y="wind_ms", labels={"ts": "Tid", "wind_ms": "Vind (m/s)"})
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig = px.bar(df, x="ts", y="precip_mm", labels={"ts": "Tid", "precip_mm": "Nederbörd (mm/3h)"})
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=60), xaxis_tickformat="%Y-%m-%d\n%H:%M")
    st.plotly_chart(fig, use_container_width=True)

st.caption("Källa: OpenWeather, uppdateringar via ditt API")
