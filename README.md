# Customer Churn & Retention Analytics

A data analytics project on the IBM Telco Customer Churn dataset. The goal was to figure out which customers are likely to churn and why, then build something useful around that — an ML model, SQL queries for business questions, an interactive dashboard, and a PDF report summarizing everything.

---

## What's in here

- **EDA notebook** — initial exploration, cleaning, visualizations
- **ML notebook** — XGBoost model with SHAP to understand which features drive churn
- **12 SQL queries** — things like revenue at risk, churn by contract type, tenure cohort analysis
- **Streamlit dashboard** — interactive filters, risk scoring, customer-level breakdown
- **PDF report** — 8-page summary you can share without running anything

The dataset has 7,032 customers and a 26.6% churn rate. The model hits ~0.86 AUC.

---

## Setup

```bash
git clone https://github.com/deveshsurana14/customer-churn-retention-analytics.git
cd customer-churn-retention-analytics
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Download the dataset from [Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) and put it at `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv`.

---

## Running things

**Notebooks first** (in order) — these generate the processed data and model:

```bash
jupyter notebook
```

Run `01_eda_churn_analysis.ipynb` then `02_model_churn_prediction.ipynb`. This creates `data/processed/customer_risk_scores.csv` which everything else depends on.

**Load into SQLite** (optional, for running the SQL files):

```bash
python load_to_sqlite.py
python run_sql_query.py sql/01_overall_churn_rate.sql
```

**Streamlit dashboard:**

```bash
streamlit run dashboard/app.py
# or just double-click run_dashboard.bat on Windows
```

**Regenerate the PDF:**

```bash
python generate_dashboard_pdf.py
```

---

## SQL queries

12 queries covering overall churn rate, churn by contract/internet service, revenue at risk, tenure cohort analysis, customer lifetime value, and a dashboard summary view.

---

## Tech stack

Python, pandas, XGBoost, SHAP, matplotlib, Streamlit, Plotly, SQLite
