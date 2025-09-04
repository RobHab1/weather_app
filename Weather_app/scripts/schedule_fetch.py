import time, os
from apscheduler.schedulers.background import BackgroundScheduler
from app.db import SessionLocal, init_db
from app.fetcher import fetch_forecast, store_forecast

CITY = os.getenv("DEFAULT_CITY", "Stockholm")

def fetch_job():
    payload = fetch_forecast(CITY)
    with SessionLocal() as db:
        store_forecast(db, CITY, payload)
    print("Uppdaterade prognos för", CITY)

if __name__ == "__main__":
    init_db()
    sched = BackgroundScheduler()
    # Kör jobbet var 3:e timme (samma upplösning som OpenWeather-prognosen)
    sched.add_job(fetch_job, 'interval', hours=3, next_run_time=None)
    sched.start()
    print("Schemalagd hämtning startad. Ctrl+C för att stoppa.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sched.shutdown()
