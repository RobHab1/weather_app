import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Anslut till databasen
engine = create_engine('sqlite:///db.sqlite')

# Läs in väderdata
df = pd.read_sql('select * from weather_obs', engine)
if df.empty:
    print('Ingen data i databasen. Kör /weather/forecast först.')
    raise SystemExit(0)

# Skapa label för "bra pass" (1) eller inte (0)
def label(row):
    score = 0
    if 8 <= row["temp_c"] <= 18: 
        score += 3
    if row["wind_ms"] < 4: 
        score += 3
    if row["precip_mm"] == 0: 
        score += 4
    return 1 if score >= 8 else 0

df["label"] = df.apply(label, axis=1)

# Features och target
X = df[["temp_c", "wind_ms", "humidity", "precip_mm"]]
y = df["label"]

# Dela i train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Träna modell
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# Utvärdera
print(classification_report(y_test, model.predict(X_test)))

# Spara modellen
joblib.dump(model, "app/ml/run_quality_model.joblib")
print("Sparade modell till app/ml/run_quality_model.joblib")
