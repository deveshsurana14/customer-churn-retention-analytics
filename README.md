# Customer Churn & Retention Analytics

An end-to-end data analytics project that predicts customer churn using machine learning, provides SQL-based business intelligence, and surfaces insights through an interactive Streamlit dashboard and a professionally designed PDF analytics report.

## Project Overview

**Dataset**: IBM Telco Customer Churn (7,032 customers)  
**Churn Rate**: 26.6%  
**Model**: XGBoost classifier with SHAP explainability  
**Risk Tiers**: Critical (≥75%), High (50–74%), Medium (25–49%), Low (<25%)

---

## Project Structure

```
customer-churn-retention-analytics/
│
├── data/
│   └── raw/                          # Original Telco CSV
│
├── notebooks/
│   ├── 01_eda_churn_analysis.ipynb   # Exploratory data analysis
│   └── 02_model_churn_prediction.ipynb # XGBoost model + SHAP
│
├── sql/                              # 12 analytical SQL queries
│   ├── 01_overall_churn_rate.sql
│   ├── 02_churn_by_contract.sql
│   ├── 03_avg_tenure_churned_vs_retained.sql
│   ├── 04_high_risk_segment.sql
│   ├── 05_revenue_at_risk.sql
│   ├── 06_churn_by_internet_service.sql
│   ├── 07_tenure_cohort_analysis.sql
│   ├── 08_customer_lifetime_value.sql
│   ├── 09_segment_risk_ranking.sql
│   ├── 10_customer_risk_scoring.sql
│   ├── 11_revenue_concentration_analysis.sql
│   └── 12_dashboard_summary_view.sql
│
├── dashboard/
│   └── app.py                        # Streamlit interactive dashboard
│
├── images/                           # Charts exported from notebooks
├── generate_dashboard_pdf.py         # PDF analytics report generator
├── load_to_sqlite.py                 # Load raw CSV into SQLite
├── run_sql_query.py                  # CLI tool to run SQL files
├── run_dashboard.bat                 # Windows launcher for Streamlit
└── requirements.txt
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/customer-churn-retention-analytics.git
cd customer-churn-retention-analytics
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the raw dataset

Download the [Telco Customer Churn dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) and place it at:

```
data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv
```

---

## Running the Project

### Step 1 — Run the notebooks (generates processed data and model)

Open Jupyter and run the two notebooks in order:

```bash
jupyter notebook
```

1. `notebooks/01_eda_churn_analysis.ipynb` — cleans data, exports charts to `images/`
2. `notebooks/02_model_churn_prediction.ipynb` — trains XGBoost, exports `data/processed/customer_risk_scores.csv` and SHAP plots

### Step 2 — Load data into SQLite

```bash
python load_to_sqlite.py
```

This creates `churn.db` from the raw CSV.

### Step 3 — Run SQL queries

```bash
python run_sql_query.py sql/01_overall_churn_rate.sql
```

Run any of the 12 SQL files to query the SQLite database directly.

### Step 4 — Launch the interactive Streamlit dashboard

```bash
# Windows (double-click or run in terminal)
run_dashboard.bat

# Or directly
streamlit run dashboard/app.py
```

The dashboard opens at `http://localhost:8501`.

### Step 5 — Generate the PDF analytics report

```bash
python generate_dashboard_pdf.py
```

Output: `reports/Customer_Churn_Analytics_Dashboard.pdf` — an 8-page professional analytics report.

---

## SQL Analytics (12 Queries)

| # | Query | Description |
|---|-------|-------------|
| 01 | Overall Churn Rate | Baseline churn percentage |
| 02 | Churn by Contract | Month-to-month vs annual impact |
| 03 | Avg Tenure by Churn | How long churners stay vs retained |
| 04 | High-Risk Segment | Customers with churn probability ≥ 75% |
| 05 | Revenue at Risk | Monthly revenue exposed to churn |
| 06 | Churn by Internet Service | Fiber vs DSL vs No Internet |
| 07 | Tenure Cohort Analysis | Churn rate across tenure buckets |
| 08 | Customer Lifetime Value | Estimated CLV per segment |
| 09 | Segment Risk Ranking | Risk tier distribution |
| 10 | Customer Risk Scoring | Full scored customer list |
| 11 | Revenue Concentration | Revenue by risk tier |
| 12 | Dashboard Summary View | Aggregated executive KPIs |

---

## PDF Dashboard Pages

The 8-page PDF covers:

1. **Command Center** — Executive KPIs and summary metrics
2. **Churn Distribution** — Breakdown by contract, tenure, internet service
3. **Risk Intelligence** — Risk tier distribution and high-risk profiles
4. **Revenue Pulse** — Revenue at risk, expected loss by segment
5. **Customer DNA** — Demographics, payment methods, charge distribution
6. **Model Performance** — ROC curve, confusion matrix, classification report
7. **SHAP Analysis** — Feature importance and explainability charts
8. **Retention War Room** — Recommended actions by risk tier

---

## Model Performance

| Metric | Value |
|--------|-------|
| ROC-AUC | ~0.86 |
| Precision (churn class) | ~0.67 |
| Recall (churn class) | ~0.78 |
| F1-Score (churn class) | ~0.72 |

---

## Tech Stack

- **Python 3.10+**
- **pandas, numpy** — data processing
- **scikit-learn, XGBoost** — machine learning
- **SHAP** — model explainability
- **matplotlib** — PDF report generation
- **Streamlit, Plotly** — interactive dashboard
- **SQLite** — SQL analytics layer
- **Jupyter** — exploratory analysis
