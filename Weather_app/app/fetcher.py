import os, requests
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from .db import WeatherObs

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def k_to_c(k):
    return k - 273.15

def mm_from_openweather(item):
    rain = item.get('rain', {})
    snow = item.get('snow', {})
    r = rain.get('3h', 0.0) if isinstance(rain, dict) else 0.0
    s = snow.get('3h', 0.0) if isinstance(snow, dict) else 0.0
    return float(r) + float(s)

def fetch_forecast(city: str):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = dict(q=city, appid=API_KEY)
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def store_forecast(db: Session, city: str, payload: dict):
    for item in payload.get('list', []):
        ts = datetime.fromtimestamp(item['dt'])
        main = item['main']
        wind = item.get('wind', {})
        obs = WeatherObs(
            city=city,
            ts=ts,
            temp_c=k_to_c(main['temp']),
            wind_ms=float(wind.get('speed', 0)),
            humidity=float(main.get('humidity', 0)),
            precip_mm=mm_from_openweather(item),
            cond=item.get('weather', [{}])[0].get('main', 'NA'),
            raw=item
        )
        db.add(obs)
    db.commit()
