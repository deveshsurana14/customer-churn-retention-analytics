WITH cohort AS (
    SELECT
        CASE
            WHEN tenure BETWEEN 0 AND 6 THEN '0-6 months'
            WHEN tenure BETWEEN 7 AND 12 THEN '7-12 months'
            WHEN tenure BETWEEN 13 AND 24 THEN '13-24 months'
            WHEN tenure BETWEEN 25 AND 48 THEN '25-48 months'
            ELSE '48+ months'
        END AS tenure_cohort,
        CASE
            WHEN tenure BETWEEN 0 AND 6 THEN 1
            WHEN tenure BETWEEN 7 AND 12 THEN 2
            WHEN tenure BETWEEN 13 AND 24 THEN 3
            WHEN tenure BETWEEN 25 AND 48 THEN 4
            ELSE 5
        END AS cohort_order,
        COUNT(*) AS total_customers,
        SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers
    FROM customers
    GROUP BY tenure_cohort, cohort_order
),
with_rate AS (
    SELECT
        tenure_cohort,
        cohort_order,
        total_customers,
        churned_customers,
        ROUND(churned_customers * 100.0 / total_customers, 2) AS churn_rate_percentage
    FROM cohort
),
with_lag AS (
    SELECT
        tenure_cohort,
        total_customers,
        churned_customers,
        churn_rate_percentage,
        LAG(churn_rate_percentage) OVER (ORDER BY cohort_order) AS previous_cohort_churn_rate,
        ROUND(
            churn_rate_percentage - LAG(churn_rate_percentage) OVER (ORDER BY cohort_order),
            2
        ) AS churn_rate_change
    FROM with_rate
)
SELECT *
FROM with_lag
ORDER BY 
    CASE tenure_cohort
        WHEN '0-6 months' THEN 1
        WHEN '7-12 months' THEN 2
        WHEN '13-24 months' THEN 3
        WHEN '25-48 months' THEN 4
        ELSE 5
    END;