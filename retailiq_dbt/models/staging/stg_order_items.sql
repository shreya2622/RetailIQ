SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    CAST(price AS FLOAT)         AS price,
    CAST(freight_value AS FLOAT) AS freight_value,
    price + freight_value        AS total_item_value
FROM {{ source('raw', 'order_items') }}