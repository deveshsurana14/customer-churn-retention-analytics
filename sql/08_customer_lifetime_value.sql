WITH clv AS (
    SELECT
        customerID,
        tenure,
        MonthlyCharges,
        TotalCharges,
        Churn,
        ROUND(MonthlyCharges * tenure, 2) AS estimated_clv,
        ROUND(MonthlyCharges * 24, 2) AS potential_2yr_value
    FROM customers
),
summary AS (
    SELECT
        Churn,
        COUNT(*) AS customers,
        ROUND(AVG(estimated_clv), 2) AS avg_clv,
        ROUND(AVG(potential_2yr_value), 2) AS avg_potential_2yr_value,
        ROUND(
            SUM(
                CASE 
                    WHEN Churn = 'Yes' 
                    THEN potential_2yr_value - estimated_clv 
                    ELSE 0 
                END
            ), 
            2
        ) AS estimated_revenue_lost
    FROM clv
    GROUP BY Churn
)
SELECT *
FROM summary;