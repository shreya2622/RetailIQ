SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_ts        AS purchased_at,
    order_approved_ts        AS approved_at,
    order_delivered_ts       AS delivered_at,
    order_delivered_carrier_ts AS delivered_carrier_at,
    order_estimated_ts       AS estimated_delivery_at
FROM {{ source('raw', 'orders') }}
WHERE order_id IS NOT NULL