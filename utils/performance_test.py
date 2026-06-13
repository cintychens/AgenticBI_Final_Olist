import time

from utils.db import run_query


BENCHMARK_CASES = [
    {
        "name": "Monthly Sales Trend",
        "question": "每个月的GMV和订单量是多少？",
        "raw_sql": """
        SELECT
            DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m') AS ym,
            COUNT(DISTINCT o.order_id) AS total_orders,
            SUM(oi.price) AS total_gmv,
            AVG(oi.price) AS avg_basket
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        WHERE o.order_purchase_timestamp IS NOT NULL
        GROUP BY ym
        ORDER BY ym
        """,
        "preagg_sql": """
        SELECT
            ym,
            total_orders,
            total_gmv,
            avg_basket
        FROM mv_monthly_sales
        ORDER BY ym
        """,
        "teacher_view": "mv_monthly_sales",
    },
    {
        "name": "State Sales Ranking",
        "question": "各州销售额排名如何？",
        "raw_sql": """
        SELECT
            c.customer_state,
            SUM(oi.price) AS total_gmv,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT c.customer_unique_id) AS unique_customers
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        JOIN customers c
            ON o.customer_id = c.customer_id
        WHERE o.order_status <> 'canceled'
        GROUP BY c.customer_state
        ORDER BY total_gmv DESC
        """,
        "preagg_sql": """
        SELECT
            customer_state,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders,
            SUM(unique_customers) AS unique_customers
        FROM mv_state_sales
        GROUP BY customer_state
        ORDER BY total_gmv DESC
        """,
        "teacher_view": "mv_state_sales",
    },
    {
        "name": "Delivery Performance",
        "question": "各州准时交付率和平均配送时长是多少？",
        "raw_sql": """
        SELECT
            c.customer_state,
            AVG(TIMESTAMPDIFF(DAY, o.order_purchase_timestamp, o.order_delivered_customer_date)) AS avg_delivery_days,
            AVG(
                CASE
                    WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
                    THEN 1
                    ELSE 0
                END
            ) AS on_time_rate,
            SUM(
                CASE
                    WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                    THEN 1
                    ELSE 0
                END
            ) AS delayed_orders
        FROM orders o
        JOIN customers c
            ON o.customer_id = c.customer_id
        WHERE o.order_delivered_customer_date IS NOT NULL
          AND o.order_estimated_delivery_date IS NOT NULL
        GROUP BY c.customer_state
        ORDER BY avg_delivery_days DESC
        """,
        "preagg_sql": """
        SELECT
            customer_state,
            AVG(avg_delivery_days) AS avg_delivery_days,
            AVG(on_time_rate) AS on_time_rate,
            SUM(delayed_orders) AS delayed_orders
        FROM mv_delivery_perf
        GROUP BY customer_state
        ORDER BY avg_delivery_days DESC
        """,
        "teacher_view": "mv_delivery_perf",
    },
    {
        "name": "Payment Distribution",
        "question": "哪种支付方式最受欢迎，平均分期数是多少？",
        "raw_sql": """
        SELECT
            p.payment_type,
            COUNT(*) AS total_transactions,
            AVG(p.payment_installments) AS avg_installments,
            SUM(p.payment_value) AS total_value
        FROM orders o
        JOIN payments p
            ON o.order_id = p.order_id
        WHERE o.order_status <> 'canceled'
          AND p.payment_type IS NOT NULL
          AND p.payment_type <> 'not_defined'
        GROUP BY p.payment_type
        ORDER BY total_transactions DESC
        """,
        "preagg_sql": """
        SELECT
            payment_type,
            SUM(total_transactions) AS total_transactions,
            AVG(avg_installments) AS avg_installments,
            SUM(total_value) AS total_value
        FROM mv_payment_dist
        WHERE payment_type IS NOT NULL
          AND payment_type <> 'not_defined'
        GROUP BY payment_type
        ORDER BY total_transactions DESC
        """,
        "teacher_view": "mv_payment_dist",
    },
    {
        "name": "Category Sales Ranking",
        "question": "Top品类销售额排名如何？",
        "raw_sql": """
        SELECT
            COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
            SUM(oi.price) AS total_gmv,
            COUNT(DISTINCT o.order_id) AS total_orders,
            AVG(oi.price) AS avg_price
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        JOIN products p
            ON oi.product_id = p.product_id
        LEFT JOIN product_category_name_translation t
            ON p.product_category_name = t.product_category_name
        WHERE o.order_status <> 'canceled'
          AND p.product_category_name IS NOT NULL
        GROUP BY product_category
        ORDER BY total_gmv DESC
        """,
        "preagg_sql": """
        SELECT
            product_category,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders,
            AVG(avg_price) AS avg_price
        FROM mv_category_sales
        WHERE product_category IS NOT NULL
        GROUP BY product_category
        ORDER BY total_gmv DESC
        """,
        "teacher_view": "mv_category_sales",
    },
]


def _measure_query(sql):
    start = time.perf_counter()
    result = run_query(sql)
    elapsed = time.perf_counter() - start
    return result, elapsed


def _benchmark_case(case):
    raw_result, raw_time = _measure_query(case["raw_sql"])
    preagg_result, preagg_time = _measure_query(case["preagg_sql"])

    speedup = round(raw_time / preagg_time, 2) if preagg_time > 0 else 0

    return {
        "name": case["name"],
        "question": case["question"],
        "teacher_view": case["teacher_view"],
        "raw_time": round(raw_time, 4),
        "view_time": round(preagg_time, 4),
        "speedup": speedup,
        "raw_rows": len(raw_result),
        "view_rows": len(preagg_result),
        "raw_sql": case["raw_sql"],
        "view_sql": case["preagg_sql"],
    }


def benchmark_all_preaggregations():
    cases = [_benchmark_case(case) for case in BENCHMARK_CASES]
    best_case = max(cases, key=lambda item: item["speedup"])
    average_speedup = round(
        sum(item["speedup"] for item in cases) / len(cases),
        2,
    )

    return {
        "cases": cases,
        "average_speedup": average_speedup,
        "best_case": best_case["name"],
        "raw_time": cases[0]["raw_time"],
        "view_time": cases[0]["view_time"],
        "speedup": cases[0]["speedup"],
        "raw_rows": cases[0]["raw_rows"],
        "view_rows": cases[0]["view_rows"],
        "raw_sql": cases[0]["raw_sql"],
        "view_sql": cases[0]["view_sql"],
    }


def ensure_monthly_sales_cache():
    return None


def benchmark_monthly_sales():
    return benchmark_all_preaggregations()
