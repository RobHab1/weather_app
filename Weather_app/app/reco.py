from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import WeatherObs

def score_slot(temp_c, wind_ms, precip_mm):
    score = 0
    # Temperaturkomfort
    if 8 <= temp_c <= 18:
        score += 3
    elif 5 <= temp_c < 8 or 18 < temp_c <= 22:
        score += 2
    elif 0 <= temp_c < 5 or 22 < temp_c <= 26:
        score += 1
    # Vind
    if wind_ms < 4:
        score += 3
    elif wind_ms < 7:
        score += 2
    elif wind_ms < 10:
        score += 1
    # Nederbörd
    if precip_mm == 0:
        score += 4
    elif precip_mm < 0.5:
        score += 2
    return score

def best_training_slots(db: Session, city: str, top_n: int = 3):
    q = select(WeatherObs).where(WeatherObs.city == city).order_by(WeatherObs.ts.asc())
    rows = db.execute(q).scalars().all()
    slots = [(r.ts.strftime('%Y-%m-%d %H:%M'), score_slot(r.temp_c, r.wind_ms, r.precip_mm)) for r in rows]
    slots.sort(key=lambda x: x[1], reverse=True)
    return [t for t,_ in slots[:top_n]]

def ice_risk_slots(db: Session, city: str):
    q = select(WeatherObs).where(WeatherObs.city == city).order_by(WeatherObs.ts.asc())
    rows = db.execute(q).scalars().all()
    return [r.ts.strftime('%Y-%m-%d %H:%M') for r in rows if r.temp_c <= 1.0 and r.precip_mm > 0]
