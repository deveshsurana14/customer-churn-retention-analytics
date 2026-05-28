WITH risk_scoring AS (
    SELECT
        customerID,
        tenure,
        MonthlyCharges,
        Contract,
        InternetService,
        Churn,
        (
            CASE WHEN Contract = 'Month-to-month' THEN 30 ELSE 0 END +
            CASE WHEN tenure < 12 THEN 25 ELSE 0 END +
            CASE WHEN MonthlyCharges > 65 THEN 20 ELSE 0 END +
            CASE WHEN InternetService = 'Fiber optic' THEN 15 ELSE 0 END +
            CASE WHEN tenure BETWEEN 12 AND 24 THEN 10 ELSE 0 END
        ) AS risk_score
    FROM customers
)
SELECT
    customerID,
    tenure,
    MonthlyCharges,
    Contract,
    InternetService,
    risk_score,
    Churn,
    CASE
        WHEN risk_score >= 70 THEN 'Critical'
        WHEN risk_score >= 45 THEN 'High'
        WHEN risk_score >= 25 THEN 'Medium'
        ELSE 'Low'
    END AS risk_tier,
    RANK() OVER (ORDER BY risk_score DESC) AS risk_rank,
    ROUND(AVG(risk_score) OVER (), 1) AS avg_risk_score
FROM risk_scoring
ORDER BY risk_score DESC;