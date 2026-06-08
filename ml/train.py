import snowflake.connector
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, classification_report
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import shap
import warnings
warnings.filterwarnings('ignore')

# ── 1. Pull features from Snowflake ──────────────────────────────────────────
conn = snowflake.connector.connect(
    user='SHREYAP',
    password='GunniShinu@1997',
    account='pvbpypn-cl36404',
    warehouse='RETAILIQ_WH',
    database='RETAILIQ',
    schema='STAGING'
)
df = pd.read_sql("SELECT * FROM rfm_features", conn)
df.columns = df.columns.str.lower()
conn.close()

print(f"Dataset shape: {df.shape}")
print(f"Churn rate: {df['is_churned'].mean():.2%}")

# ── 2. Feature engineering ────────────────────────────────────────────────────
# Encode categorical features
le = LabelEncoder()
df['customer_state_enc'] = le.fit_transform(df['customer_state'].fillna('unknown'))
df['preferred_payment_enc'] = le.fit_transform(df['preferred_payment'].fillna('unknown'))

FEATURES = [
    'recency_days',
    'frequency',
    'monetary_value',
    'avg_order_value',
    'avg_review_score',
    'avg_installments',
    'customer_lifespan_days',
    'customer_state_enc',
    'preferred_payment_enc',
]

TARGET = 'is_churned'

X = df[FEATURES].fillna(0)
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train size: {len(X_train):,}  |  Test size: {len(X_test):,}")

# ── 3. Train with MLflow tracking ─────────────────────────────────────────────
mlflow.set_experiment("retailiq_churn")

models = {
    "XGBoost": XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        random_state=42,
        eval_metric='auc',
        verbosity=0
    ),
    "LightGBM": LGBMClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        class_weight='balanced',
        random_state=42,
        verbose=-1
    )
}

best_roc  = 0
best_name = None
best_model = None

for name, model in models.items():
    with mlflow.start_run(run_name=name):

        model.fit(X_train, y_train)
        preds = model.predict_proba(X_test)[:, 1]
        roc   = roc_auc_score(y_test, preds)

        # Log params and metrics
        mlflow.log_param("model_type",   name)
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth",    5)
        mlflow.log_metric("roc_auc",     roc)

        # Log the model itself
        mlflow.sklearn.log_model(model, artifact_path="model",
                                 registered_model_name=f"retailiq_{name.lower()}")

        print(f"\n{name}  →  ROC-AUC: {roc:.4f}")
        print(classification_report(y_test, model.predict(X_test)))

        if roc > best_roc:
            best_roc   = roc
            best_name  = name
            best_model = model

print(f"\nBest model: {best_name}  (ROC-AUC: {best_roc:.4f})")

# ── 4. SHAP analysis on best model ────────────────────────────────────────────
print("\nRunning SHAP analysis...")
explainer   = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_test)

# Mean absolute SHAP values = feature importance
shap_importance = pd.DataFrame({
    'feature':    FEATURES,
    'importance': np.abs(shap_values).mean(axis=0)
}).sort_values('importance', ascending=False)

print("\nTop feature importances:")
print(shap_importance.to_string(index=False))

# Save model and metadata for API
import joblib, os
os.makedirs('ml/artifacts', exist_ok=True)
joblib.dump(best_model,    'ml/artifacts/model.pkl')
joblib.dump(FEATURES,      'ml/artifacts/features.pkl')
joblib.dump(shap_importance, 'ml/artifacts/shap_importance.pkl')
print("\nModel artifacts saved to ml/artifacts/")