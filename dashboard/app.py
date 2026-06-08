import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
import requests
import joblib

st.set_page_config(page_title="RetailIQ Dashboard", layout="wide")
st.title("RetailIQ — Customer Intelligence & Churn Analytics")

@st.cache_data
def load_data():
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
    return df

df = load_data()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers",  f"{len(df):,}")
col2.metric("Churn Rate",       f"{df['is_churned'].mean():.1%}")
col3.metric("Avg Order Value",  f"${df['avg_order_value'].mean():.2f}")
col4.metric("Avg Review Score", f"{df['avg_review_score'].mean():.2f}")

st.markdown("---")

# ── RFM Distributions ─────────────────────────────────────────────────────────
st.subheader("RFM Feature Distributions")
col_a, col_b, col_c = st.columns(3)

with col_a:
    fig = px.histogram(df, x='recency_days', nbins=50,
                       title='Recency (days since last order)',
                       color_discrete_sequence=['#636EFA'])
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    fig = px.histogram(df, x='frequency', nbins=20,
                       title='Frequency (orders per customer)',
                       color_discrete_sequence=['#EF553B'])
    st.plotly_chart(fig, use_container_width=True)

with col_c:
    fig = px.histogram(df, x='monetary_value', nbins=50,
                       title='Monetary Value (total spend $)',
                       color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig, use_container_width=True)

# ── Churn by State ────────────────────────────────────────────────────────────
st.subheader("Churn Rate by State")
churn_state = df.groupby('customer_state')['is_churned'].mean().reset_index()
churn_state.columns = ['state', 'churn_rate']
churn_state = churn_state.sort_values('churn_rate', ascending=False)
fig = px.bar(churn_state, x='state', y='churn_rate',
             color='churn_rate', color_continuous_scale='Reds',
             title='Churn Rate by Brazilian State')
fig.update_layout(yaxis_tickformat='.0%')
st.plotly_chart(fig, use_container_width=True)

# ── SHAP Feature Importance ───────────────────────────────────────────────────
st.subheader("Model Feature Importance (SHAP)")
try:
    shap_df = joblib.load('ml/artifacts/shap_importance.pkl')
    fig = px.bar(shap_df, x='importance', y='feature', orientation='h',
                 title='Mean |SHAP| Values — Top Churn Drivers',
                 color='importance', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
except:
    st.info("SHAP artifacts not found.")

# ── Live Prediction Widget ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Live Churn Prediction")

c1, c2, c3 = st.columns(3)
recency      = c1.slider("Recency (days)",          0, 730, 90)
frequency    = c2.slider("Frequency (# orders)",    1, 20,  1)
monetary     = c3.number_input("Total Spend ($)",   0.0, 5000.0, 150.0)
review       = c1.slider("Avg Review Score",        1.0, 5.0, 4.0)
lifespan     = c2.slider("Customer Lifespan (days)",0, 730, 30)
installments = c3.slider("Avg Installments",        1, 12, 1)

if st.button("Predict Churn Risk"):
    payload = {
        "recency_days":           recency,
        "frequency":              frequency,
        "monetary_value":         monetary,
        "avg_order_value":        monetary / max(frequency, 1),
        "avg_review_score":       review,
        "avg_installments":       installments,
        "customer_lifespan_days": lifespan,
        "customer_state_enc":     5,
        "preferred_payment_enc":  1
    }
    try:
        response = requests.post("http://localhost:8000/predict", json=payload)
        result   = response.json()
        prob     = result['churn_probability']

        col_r1, col_r2 = st.columns(2)
        fig_gauge = go.Figure(go.Indicator(
            mode  = "gauge+number",
            value = prob * 100,
            title = {'text': "Churn Probability (%)"},
            gauge = {
                'axis':  {'range': [0, 100]},
                'bar':   {'color': "red" if prob > 0.5 else "green"},
                'steps': [
                    {'range': [0,  50],  'color': "#d4edda"},
                    {'range': [50, 75],  'color': "#fff3cd"},
                    {'range': [75, 100], 'color': "#f8d7da"},
                ]
            }
        ))
        col_r1.plotly_chart(fig_gauge, use_container_width=True)
        col_r2.markdown(f"### Prediction: **{result['prediction'].upper()}**")
        col_r2.markdown("**Top 3 Risk Factors:**")
        for factor in result['top_3_risk_factors']:
            direction = "↑ increases" if factor['impact'] > 0 else "↓ decreases"
            col_r2.write(f"- **{factor['feature']}** {direction} churn risk")

    except Exception as e:
        st.error(f"Start the FastAPI server first. ({e})")