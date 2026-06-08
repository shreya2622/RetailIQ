WITH base AS (SELECT * FROM {{ ref('customer_orders') }}),

ref_date AS (
    SELECT DATEADD(day, 1, MAX(purchased_at)) AS ref_dt FROM base
),

rfm AS (
    SELECT
        b.customer_unique_id,
        b.customer_state,

        DATEDIFF(day, MAX(b.purchased_at), r.ref_dt)  AS recency_days,
        COUNT(DISTINCT b.order_id)                     AS frequency,
        SUM(b.total_payment)                           AS monetary_value,
        AVG(b.total_payment)                           AS avg_order_value,
        AVG(b.avg_review_score)                        AS avg_review_score,
        MAX(b.primary_payment_type)                    AS preferred_payment,
        AVG(b.installments)                            AS avg_installments,
        DATEDIFF(day, MIN(b.purchased_at),
                      MAX(b.purchased_at))             AS customer_lifespan_days,

        CASE
            WHEN DATEDIFF(day, MAX(b.purchased_at), r.ref_dt) > 180
            THEN 1 ELSE 0
        END AS is_churned

    FROM base b
    CROSS JOIN ref_date r
    GROUP BY b.customer_unique_id, b.customer_state, r.ref_dt
)

SELECT * FROM rfm