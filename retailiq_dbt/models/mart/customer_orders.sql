WITH orders AS (SELECT * FROM {{ ref('stg_orders') }}),
     items   AS (SELECT * FROM {{ ref('stg_order_items') }}),
     pays    AS (SELECT * FROM {{ ref('stg_payments') }}),
     reviews AS (SELECT * FROM {{ ref('stg_reviews') }}),
     custs   AS (SELECT * FROM {{ ref('stg_customers') }})

SELECT
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_id,
    o.order_status,
    o.purchased_at,
    o.delivered_at,
    i.price,
    i.freight_value,
    i.total_item_value,
    p.total_payment,
    p.installments,
    p.primary_payment_type,
    r.avg_review_score
FROM orders o
LEFT JOIN items   i ON o.order_id = i.order_id
LEFT JOIN pays    p ON o.order_id = p.order_id
LEFT JOIN reviews r ON o.order_id = r.order_id
LEFT JOIN custs   c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'