WITH segment_stats AS (
    SELECT
        Contract,
        InternetService,
        COUNT(*) AS total_customers,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
        ROUND(
            SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
            2
        ) AS churn_rate_percentage
    FROM customers
    GROUP BY Contract, InternetService
)
SELECT
    Contract,
    InternetService,
    total_customers,
    churned_customers,
    churn_rate_percentage,
    RANK() OVER (ORDER BY churn_rate_percentage DESC) AS risk_rank,
    NTILE(4) OVER (ORDER BY churn_rate_percentage DESC) AS risk_quartile,
    ROUND(
        churn_rate_percentage - AVG(churn_rate_percentage) OVER (), 
        2
    ) AS deviation_from_avg_churn
FROM segment_stats
ORDER BY risk_rank;