import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .db import init_db, SessionLocal, WeatherObs
from .fetcher import fetch_forecast, store_forecast
from .schemas import WeatherPoint, Recommendation, IceAlert
from .reco import best_training_slots, ice_risk_slots

app = FastAPI(title="Weather BI/ML API")

# Tillåt CORS (så frontend kan anropa API:t)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initiera databasen
init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/weather/forecast")
def get_forecast(city: str = Query(default=os.getenv("DEFAULT_CITY", "Stockholm"))):
    payload = fetch_forecast(city)
    with SessionLocal() as db:
        store_forecast(db, city, payload)
    return {"saved_points": len(payload.get("list", []))}

@app.get("/weather/current")
def get_current(city: str = Query(default=os.getenv("DEFAULT_CITY", "Stockholm"))):
    with SessionLocal() as db:
        q = select(WeatherObs).where(WeatherObs.city == city).order_by(WeatherObs.ts.desc())
        row = db.execute(q).scalars().first()
        if not row:
            return {"detail": "No data. Call /weather/forecast first."}
        return WeatherPoint(
            time=row.ts.isoformat(),
            temp_c=row.temp_c,
            wind_ms=row.wind_ms,
            humidity=row.humidity,
            precip_mm=row.precip_mm,
            cond=row.cond
        )

@app.get("/recommendations/run")
def recommend_run(city: str = Query(default=os.getenv("DEFAULT_CITY", "Stockholm"))):
    with SessionLocal() as db:
        slots = best_training_slots(db, city, top_n=3)
    return Recommendation(best_slots=slots, reason="Torrt, låg vind, 8–18°C")

@app.get("/alerts/ice")
def alerts_ice(city: str = Query(default=os.getenv("DEFAULT_CITY", "Stockholm"))):
    with SessionLocal() as db:
        slots = ice_risk_slots(db, city)
    return IceAlert(risk_slots=slots, rule="Temp ≤ 1°C och nederbörd > 0 mm")
@app.get("/")
def root():
    return {"message": "API lever. Gå till /docs eller /weather/forecast?city=Stockholm"}
