WITH base AS (
    SELECT
        *,
        CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END AS is_churned,
        CASE
            WHEN tenure <= 12 THEN 'New (0-12m)'
            WHEN tenure <= 24 THEN 'Growing (13-24m)'
            WHEN tenure <= 48 THEN 'Mature (25-48m)'
            ELSE 'Loyal (48m+)'
        END AS tenure_segment
    FROM customers
),
segment_summary AS (
    SELECT
        tenure_segment,
        Contract,
        COUNT(*) AS total_customers,
        SUM(is_churned) AS churned_customers,
        ROUND(SUM(is_churned) * 100.0 / COUNT(*), 2) AS churn_rate_percentage,
        ROUND(AVG(MonthlyCharges), 2) AS avg_monthly_charge,
        ROUND(
            SUM(CASE WHEN is_churned = 1 THEN MonthlyCharges ELSE 0 END), 
            2
        ) AS monthly_revenue_at_risk
    FROM base
    GROUP BY tenure_segment, Contract
),
ranked AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY tenure_segment 
            ORDER BY churn_rate_percentage DESC
        ) AS rank_within_segment,
        ROUND(monthly_revenue_at_risk * 12, 2) AS annual_revenue_at_risk,
        ROUND(
            SUM(monthly_revenue_at_risk) OVER (PARTITION BY tenure_segment), 
            2
        ) AS segment_total_revenue_at_risk
    FROM segment_summary
)
SELECT *
FROM ranked
ORDER BY annual_revenue_at_risk DESC;