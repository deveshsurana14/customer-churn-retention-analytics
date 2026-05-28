SELECT 
    COUNT(*) AS high_risk_customers,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charges,
    ROUND(SUM(MonthlyCharges), 2) AS monthly_revenue_at_risk
FROM customers
WHERE Contract = 'Month-to-month'
  AND MonthlyCharges > 65;