import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import requests

from app.db import Base, init_db, WeatherObs
from app.fetcher import fetch_forecast, store_forecast

# Ladda .env (API-nyckel mm)
load_dotenv()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Setup
st.set_page_config(page_title="Väderdashboard", page_icon="☀️", layout="wide")
engine = create_engine('sqlite:///db.sqlite', echo=False)
init_db()  # skapar tabeller om de saknas

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
div[data-testid="stMetricValue"] {font-size: 28px;}
div[data-testid="stMetricDelta"] {font-size: 14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data(city: str) -> pd.DataFrame:
    q = f"SELECT * FROM weather_obs WHERE city = '{city}' ORDER BY ts"
    df = pd.read_sql(q, engine)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"])
    return df

def update_city(city: str):
    try:
        payload = fetch_forecast(city)
        with Session(engine) as db:
            store_forecast(db, city, payload)
        return {"ok": True, "saved_points": len(payload.get("list", []))}
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

# UI
st.title("Väderdashboard")

with st.sidebar:
    cities = st.multiselect(
        "Välj städer", 
        ["Stockholm", "Göteborg", "Malmö", "Uppsala"], 
        default=["Stockholm"]
    )
    if st.button("Uppdatera prognos"):
        for city in cities:
            res = update_city(city)
            st.toast(
                f"{city}: {res}" if "ok" in res else f"{city} FEL: {res}",
                icon="✅" if "ok" in res else "⚠️"
            )
        load_data.clear()  # rensa cache

# Visa dashboards för alla valda städer
for city in cities:
    st.header(f"Prognos för {city}")
    df = load_data(city)

    if df.empty:
        st.warning("Ingen data ännu. Klicka på Uppdatera prognos.")
        continue

    # Filter period
    date_min = df["ts"].min().date()
    date_max = df["ts"].max().date()
    start_date, end_date = st.slider(
        f"Period för {city}",
        min_value=date_min, max_value=date_max,
        value=(date_min, date_max), format="YYYY-MM-DD",
        key=f"slider_{city}"
    )
    mask = (df["ts"].dt.date >= start_date) & (df["ts"].dt.date <= end_date)
    df = df.loc[mask].reset_index(drop=True)

    # KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mätpunkter", len(df))
    col2.metric("Medeltemp °C", f"{df['temp_c'].mean():.1f}")
    col3.metric("Max vind m/s", f"{df['wind_ms'].max():.1f}")
    col4.metric("Andel torra %", f"{(df['precip_mm'].eq(0).mean()*100):.0f}")

    tab1, tab2, tab3, tab4 = st.tabs(["Översikt", "Temperatur", "Vind", "Nederbörd"])

    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Bästa tider för promenad/träning")
            reco = get_reco(city)
            slots = reco.get("best_slots", [])
            if slots:
                st.write("\n".join(f"• {s}" for s in slots))
            else:
                st.info("Inga förslag just nu.")

        with c2:
            st.subheader("Halkrisk")
            ice = get_ice(city)
            risks = ice.get("risk_slots", [])
            if risks:
                st.error("\n".join(f"• {s}" for s in risks))
            else:
                st.success("Ingen risk i perioden.")

        st.markdown("---")
        st.dataframe(df.head(20))  # visar rådata

    with tab2:
        fig = px.line(df, x="ts", y="temp_c", labels={"ts": "Tid", "temp_c": "Temp (°C)"})
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.line(df, x="ts", y="wind_ms", labels={"ts": "Tid", "wind_ms": "Vind (m/s)"})
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        fig = px.bar(df, x="ts", y="precip_mm", labels={"ts": "Tid", "precip_mm": "Nederbörd (mm/3h)"})
        st.plotly_chart(fig, use_container_width=True)

st.caption("Källa: OpenWeather API + egna analyser")
