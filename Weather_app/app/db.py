from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Skapa databasen (SQLite, sparas som db.sqlite i projektmappen)
engine = create_engine('sqlite:///db.sqlite', echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# Modell för väderobservationer
class WeatherObs(Base):
    __tablename__ = 'weather_obs'
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    ts = Column(DateTime, index=True)
    temp_c = Column(Float)
    wind_ms = Column(Float)
    humidity = Column(Float)
    precip_mm = Column(Float)
    cond = Column(String)
    raw = Column(JSON)

def init_db():
    Base.metadata.create_all(bind=engine)
