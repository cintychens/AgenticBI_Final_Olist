import time

from utils.db import run_query


def benchmark_monthly_sales():

    # =====================
    # 原始表 JOIN 查询
    # =====================

    raw_sql = """
    SELECT
        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%%Y-%%m'
        ) AS ym,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.price) AS total_gmv,
        AVG(oi.price) AS avg_basket
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY ym
    ORDER BY ym
    """

    # =====================
    # 预聚合视图查询
    # =====================

    view_sql = """
    SELECT *
    FROM agg_monthly_sales
    """

    # =====================
    # 原始表耗时
    # =====================

    raw_start = time.perf_counter()

    raw_result = run_query(raw_sql)

    raw_time = time.perf_counter() - raw_start

    # =====================
    # 视图耗时
    # =====================

    view_start = time.perf_counter()

    view_result = run_query(view_sql)

    view_time = time.perf_counter() - view_start

    # =====================
    # 加速倍数
    # =====================

    if view_time > 0:

        speedup = round(
            raw_time / view_time,
            2
        )

    else:

        speedup = 0

    return {

        "raw_time":
            round(raw_time, 4),

        "view_time":
            round(view_time, 4),

        "speedup":
            speedup,

        "raw_rows":
            len(raw_result),

        "view_rows":
            len(view_result),

        "raw_sql":
            raw_sql,

        "view_sql":
            view_sql,

    }