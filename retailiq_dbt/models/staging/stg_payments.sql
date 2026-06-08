SELECT
    order_id,
    SUM(payment_value)            AS total_payment,
    MAX(payment_installments)     AS installments,
    MAX(payment_type)             AS primary_payment_type
FROM {{ source('raw', 'order_payments') }}
GROUP BY order_id