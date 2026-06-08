SELECT
    order_id,
    AVG(review_score) AS avg_review_score
FROM {{ source('raw', 'order_reviews') }}
GROUP BY order_id