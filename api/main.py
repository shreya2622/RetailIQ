from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import shap
import pandas as pd

app = FastAPI(title="RetailIQ Churn API")

model           = joblib.load("ml/artifacts/model.pkl")
FEATURES        = joblib.load("ml/artifacts/features.pkl")
shap_importance = joblib.load("ml/artifacts/shap_importance.pkl")
explainer       = shap.TreeExplainer(model)

class CustomerFeatures(BaseModel):
    recency_days:           float
    frequency:              float
    monetary_value:         float
    avg_order_value:        float
    avg_review_score:       float
    avg_installments:       float
    customer_lifespan_days: float
    customer_state_enc:     float
    preferred_payment_enc:  float

@app.get("/")
def health():
    return {"status": "ok", "model": "RetailIQ Churn Classifier"}

@app.post("/predict")
def predict(customer: CustomerFeatures):
    X = pd.DataFrame([customer.dict()])[FEATURES]

    churn_probability = float(model.predict_proba(X)[0][1])
    prediction        = "churned" if churn_probability >= 0.5 else "active"

    shap_vals   = explainer.shap_values(X)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    shap_vals = np.array(shap_vals).flatten()

    top_factors = pd.DataFrame({
        'feature':    FEATURES,
        'shap_value': shap_vals
    }).iloc[np.abs(shap_vals).argsort()[::-1]].head(3)

    risk_factors = [
        {"feature": row["feature"], "impact": round(row["shap_value"], 4)}
        for _, row in top_factors.iterrows()
    ]

    return {
        "churn_probability":  round(churn_probability, 4),
        "prediction":         prediction,
        "top_3_risk_factors": risk_factors
    }