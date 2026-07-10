import os
import joblib
import numpy as np

_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models")

_response_model = None
_response_scaler = None
_completion_model = None


def get_response_model():
    global _response_model, _response_scaler
    if _response_model is None:
        _response_model = joblib.load(os.path.join(_MODELS_DIR, "response_model.pkl"))
        _response_scaler = joblib.load(os.path.join(_MODELS_DIR, "response_scaler.pkl"))
    return _response_model, _response_scaler


def get_completion_model():
    global _completion_model
    if _completion_model is None:
        _completion_model = joblib.load(os.path.join(_MODELS_DIR, "completion_model.pkl"))
    return _completion_model


def predict_response_likelihood(
    screening_score: float,
    match_score: float,
    experience_years: int
) -> float:
    model, scaler = get_response_model()
    X = np.array([[screening_score,
                   match_score,
                   experience_years]])
    X_scaled = scaler.transform(X)
    prob = model.predict_proba(X_scaled)[0][1]
    return round(float(prob), 2)


def predict_completion_likelihood(
    match_score: float,
    screening_score: float,
    experience_years: int,
    session_hour: int = 10
) -> float:
    model = get_completion_model()
    X = np.array([[match_score, screening_score,
                   experience_years, session_hour]])
    prob = model.predict_proba(X)[0][1]
    return round(float(prob), 2)


def interpret(likelihood: float) -> str:
    if likelihood > 0.7:
        return "High"
    if likelihood >= 0.4:
        return "Medium"
    return "Low"
