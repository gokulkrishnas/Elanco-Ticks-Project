import sqlite3
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
import math
import joblib

DB_PATH = "tick_sightings.db"
MODEL_PATH = "tick_forecast_model.pkl"

def train_model():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT year, month, COUNT(*) AS count
        FROM sightings
        WHERE year != '' AND month != ''
        GROUP BY year, month
        ORDER BY CAST(year AS INTEGER), 
         CASE month 
             WHEN 'January' THEN 1
             WHEN 'February' THEN 2
             WHEN 'March' THEN 3
             WHEN 'April' THEN 4
             WHEN 'May' THEN 5
             WHEN 'June' THEN 6
             WHEN 'July' THEN 7
             WHEN 'August' THEN 8
             WHEN 'September' THEN 9
             WHEN 'October' THEN 10
             WHEN 'November' THEN 11
             WHEN 'December' THEN 12
         END
    """)

    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 3:
        raise ValueError("Not enough data to train")

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    data = []
    for r in rows:
        year, month, count = r
        m_num = month_map.get(month, 0)
        if m_num > 0:
            data.append((int(year), int(m_num), count))

    # Create time index
    X = np.arange(len(data)).reshape(-1, 1)
    y = np.array([d[2] for d in data])

    # Build pipeline
    model = Pipeline([
        ("poly", PolynomialFeatures(degree=2)),
        ("ridge", Ridge(alpha=1.0))
    ])

    model.fit(X, y)

    joblib.dump({
        "model": model,
        "data_len": len(data),
        "last_year": data[-1][0],
        "last_month": data[-1][1]
    }, MODEL_PATH)

    print("Model trained and saved to", MODEL_PATH)


if __name__ == "__main__":
    train_model()