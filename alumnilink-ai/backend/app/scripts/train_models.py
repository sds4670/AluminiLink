"""
Trains the two Module 6 predictive models on synthetic seed data and saves
them to backend/models/ (joblib .pkl files, loaded lazily by
app.services.ml.predict).

Usage:
    docker compose exec backend python -m app.scripts.train_models

Also run automatically at image build time (see Dockerfile) so a freshly
built image ships with trained models; re-run manually after a `docker
compose up` in this dev setup since `./backend:/app` is bind-mounted and
overlays whatever the build step produced.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")


def train_response_model():
    # Features: screening_score, match_score,
    # alumni experience_years, student
    # graduation_year
    # Target: 1 if request accepted, 0 if rejected

    # Generate synthetic training data from
    # connection_requests + match_scores tables
    # For seed data use the 30 requests in CSV
    # Label: expected_status == PASS →
    # higher probability of acceptance

    data = {
        "screening_score": [0.82,0.78,0.91,0.75,
            0.88,0.72,0.85,0.76,0.83,0.79,
            0.38,0.31,0.42,0.35,0.28,0.77,
            0.81,0.74,0.86,0.80,0.33,0.29,
            0.44,0.36,0.27,0.73,0.87,0.76,
            0.82,0.78],
        "match_score": [0.75,0.68,0.82,0.71,
            0.79,0.65,0.80,0.69,0.77,0.73,
            0.45,0.38,0.50,0.42,0.35,0.72,
            0.78,0.67,0.83,0.74,0.40,0.33,
            0.48,0.39,0.30,0.70,0.81,0.71,
            0.76,0.72],
        "experience_years": [6,8,10,14,7,9,12,
            11,9,13,6,8,10,14,7,9,12,11,
            9,13,6,8,10,14,7,9,12,11,9,13],
        "accepted": [1,1,1,1,1,1,1,1,1,1,
            0,0,0,0,0,1,1,1,1,1,
            0,0,0,0,0,1,1,1,1,1]
    }

    df = pd.DataFrame(data)
    X = df[["screening_score","match_score",
            "experience_years"]]
    y = df["accepted"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(random_state=42)
    model.fit(X_scaled, y)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_DIR, "response_model.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "response_scaler.pkl"))
    print("Response model trained and saved")
    return model


def train_completion_model():
    # Features: match_score, screening_score,
    # alumni experience_years, session hour
    # Target: 1 if completed, 0 if cancelled

    data = {
        "match_score": [0.75,0.82,0.71,0.79,
            0.65,0.80,0.69,0.77,0.73,0.68,
            0.45,0.50,0.42,0.35,0.72,0.78,
            0.67,0.83,0.74,0.70],
        "screening_score": [0.82,0.91,0.75,0.88,
            0.72,0.85,0.76,0.83,0.79,0.78,
            0.38,0.42,0.35,0.28,0.77,0.81,
            0.74,0.86,0.80,0.73],
        "experience_years": [6,10,14,7,9,12,11,
            9,13,8,6,10,14,7,9,12,11,9,13,8],
        "session_hour": [10,11,14,9,15,10,11,
            14,9,15,10,11,14,9,15,10,11,
            14,9,15],
        "completed": [1,1,1,1,1,1,1,1,1,1,
            1,1,1,1,1,0,0,1,1,0]
    }

    df = pd.DataFrame(data)
    X = df[["match_score","screening_score",
            "experience_years","session_hour"]]
    y = df["completed"]

    model = RandomForestClassifier(
        n_estimators=10, random_state=42
    )
    model.fit(X, y)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model,
        os.path.join(MODELS_DIR, "completion_model.pkl"))
    print("Completion model trained and saved")
    return model


if __name__ == "__main__":
    train_response_model()
    train_completion_model()
