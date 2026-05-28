WITH customer_revenue AS (
    SELECT
        customerID,
        Churn,
        MonthlyCharges,
        SUM(MonthlyCharges) OVER () AS total_monthly_revenue,
        ROUND(MonthlyCharges * 100.0 / SUM(MonthlyCharges) OVER (), 4) AS revenue_share_percentage,
        NTILE(100) OVER (ORDER BY MonthlyCharges DESC) AS revenue_percentile
    FROM customers
),
cumulative AS (
    SELECT
        *,
        SUM(revenue_share_percentage) OVER (
            ORDER BY MonthlyCharges DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue_percentage
    FROM customer_revenue
)
SELECT
    revenue_percentile,
    COUNT(*) AS customers_in_percentile,
    ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charge,
    ROUND(MAX(cumulative_revenue_percentage), 2) AS cumulative_revenue_percentage,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers_in_group
FROM cumulative
WHERE revenue_percentile <= 20
GROUP BY revenue_percentile
ORDER BY revenue_percentile;