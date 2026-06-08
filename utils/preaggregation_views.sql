CREATE OR REPLACE VIEW mv_monthly_sales AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    SUM(oi.price) AS total_gmv,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.price) / NULLIF(COUNT(DISTINCT o.order_id), 0) AS avg_basket,
    SUM(oi.freight_value) AS total_freight
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status <> 'canceled'
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m');

CREATE OR REPLACE VIEW mv_state_sales AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    c.customer_state,
    SUM(oi.price) AS total_gmv,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT c.customer_unique_id) AS unique_customers
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status <> 'canceled'
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'), c.customer_state;

CREATE OR REPLACE VIEW mv_category_sales AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
    SUM(oi.price) AS total_gmv,
    COUNT(DISTINCT o.order_id) AS total_orders,
    AVG(oi.price) AS avg_price
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
LEFT JOIN product_category_name_translation t
    ON p.product_category_name = t.product_category_name
WHERE o.order_status <> 'canceled'
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'), product_category;

CREATE OR REPLACE VIEW mv_delivery_perf AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    c.customer_state,
    AVG(TIMESTAMPDIFF(DAY, o.order_purchase_timestamp, o.order_delivered_customer_date)) AS avg_delivery_days,
    AVG(CASE
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 1
        ELSE 0
    END) AS on_time_rate,
    SUM(CASE
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1
        ELSE 0
    END) AS delayed_orders
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'), c.customer_state;

CREATE OR REPLACE VIEW mv_seller_perf AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    s.seller_id,
    s.seller_state,
    SUM(oi.price) AS total_gmv,
    COUNT(DISTINCT o.order_id) AS total_orders,
    AVG(r.review_score) AS avg_review_score
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
LEFT JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_status <> 'canceled'
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'), s.seller_id, s.seller_state;

CREATE OR REPLACE VIEW mv_payment_dist AS
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS ym,
    p.payment_type,
    COUNT(*) AS total_transactions,
    AVG(p.payment_installments) AS avg_installments,
    SUM(p.payment_value) AS total_value
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.order_status <> 'canceled'
GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m'), p.payment_type;
