from pydantic import BaseModel
from typing import List

# Data som returneras från API
class WeatherPoint(BaseModel):
    time: str
    temp_c: float
    wind_ms: float
    humidity: float
    precip_mm: float
    cond: str

class Recommendation(BaseModel):
    best_slots: List[str]
    reason: str

class IceAlert(BaseModel):
    risk_slots: List[str]
    rule: str
