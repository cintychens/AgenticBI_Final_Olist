from utils.db import run_query
from agents.llm_agent import classify_question
from models.forecast_model import forecast_sales

VIEW_MAPPING = {
    "sales": "mv_monthly_sales",
    "state": "mv_state_sales",
    "category": "mv_category_sales",
    "delivery": "mv_delivery_perf",
    "payment": "mv_payment_dist",
    "seller": "mv_seller_perf",
    "review": "order_reviews",
}


def select_best_view(question):

    intent = classify_question(question)

    print(f"[LLM INTENT] {intent}")

    return VIEW_MAPPING.get(intent)


def generate_sql(view_name, question):

    if view_name == "mv_monthly_sales":

        return """
        SELECT
            ym,
            total_gmv,
            total_orders,
            avg_basket
        FROM mv_monthly_sales
        ORDER BY ym
        """

    elif view_name == "mv_state_sales":

        return """
        SELECT
            customer_state,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders
        FROM mv_state_sales
        GROUP BY customer_state
        ORDER BY total_gmv DESC
        LIMIT 10
        """

    elif view_name == "mv_category_sales":

        return """
        SELECT
            product_category,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders,
            AVG(avg_price) AS avg_price
        FROM mv_category_sales
        WHERE product_category IS NOT NULL
        GROUP BY product_category
        ORDER BY total_gmv DESC
        LIMIT 10
        """

    elif view_name == "mv_delivery_perf":

        return """
        SELECT
            customer_state,
            ROUND(AVG(avg_delivery_days), 2) AS avg_delivery_days,
            ROUND(AVG(on_time_rate), 4) AS on_time_rate,
            SUM(delayed_orders) AS delayed_orders
        FROM mv_delivery_perf
        GROUP BY customer_state
        ORDER BY avg_delivery_days DESC
        LIMIT 10
        """

    elif view_name == "mv_payment_dist":

        return """
        SELECT
            payment_type,
            SUM(total_transactions) AS total_transactions,
            ROUND(AVG(avg_installments), 2) AS avg_installments,
            SUM(total_value) AS total_value
        FROM mv_payment_dist
        GROUP BY payment_type
        ORDER BY total_transactions DESC
        """

    elif view_name == "mv_seller_perf":

        return """
        SELECT
            seller_id,
            seller_state,
            total_gmv,
            total_orders,
            avg_review_score
        FROM mv_seller_perf
        WHERE avg_review_score IS NOT NULL
        ORDER BY avg_review_score ASC
        LIMIT 10
        """

    elif view_name == "order_reviews":

        return """
        SELECT
           review_score,
           review_comment_message
        FROM order_reviews
        WHERE
            review_comment_message IS NOT NULL
            AND review_comment_message <> ''
        LIMIT 5000
        """

    return None


def analyze_question(question):

    # 自动选择 View
    view_name = select_best_view(question)

    # 命中预聚合视图
    if view_name:

        sql = generate_sql(view_name, question)

        print(f"[INFO] Using View: {view_name}")

    # 回退机制
    else:

        sql = """
        SELECT *
        FROM orders
        LIMIT 10
        """

        print("[INFO] Fallback to Base Table")

    # 执行SQL
    result = run_query(sql)

    return result


def analyze_question_with_trace(question):

    intent = classify_question(question)

    print(f"[LLM INTENT] {intent}")

    forecast = None

    if intent == "forecast":

        sql = """
        SELECT
            ym,
            total_gmv,
            total_orders,
            avg_basket
        FROM mv_monthly_sales
        ORDER BY ym
        """

        result = run_query(sql)

        forecast = forecast_sales()

        view_name = "mv_monthly_sales"

        print("[INFO] Forecast Agent triggered")

    else:

        view_name = VIEW_MAPPING.get(intent)

        print(f"[VIEW] {view_name}")

        if view_name:

            sql = generate_sql(view_name, question)

            print(f"[INFO] Using View: {view_name}")

        else:

            sql = """
            SELECT *
            FROM orders
            LIMIT 10
            """

            print("[INFO] Fallback to Base Table")

        result = run_query(sql)

    # =====================
    # 多图表查询集合
    # =====================

    queries = {"main_query": {"view": view_name, "sql": sql, "data": result}}

    # =====================
    # 评论分析 -> 词云数据
    # =====================
    if intent == "review":

        review_data = query_review_texts()

        queries["base_review_insight"] = {
            "view": "order_reviews",
            "sql": "review insight",
            "data": review_data,
        }

        positive_reviews = review_data[review_data["review_score"] >= 4]

        negative_reviews = review_data[review_data["review_score"] <= 2]

        queries["positive_wordcloud"] = {
            "view": "positive_reviews",
            "sql": "positive wordcloud",
            "data": positive_reviews,
        }

        queries["negative_wordcloud"] = {
            "view": "negative_reviews",
            "sql": "negative wordcloud",
            "data": negative_reviews,
        }

        print("[INFO] Positive WordCloud Loaded")

        print("[INFO] Negative WordCloud Loaded")

    # =====================
    # 配送分析 -> 重量运费散点图
    # =====================

    if intent == "delivery":

        try:

            scatter_data = query_weight_freight_scatter()

            queries["weight_freight_scatter"] = {
                "view": "products+order_items+orders",
                "sql": """
                weight vs freight scatter
                """,
                "data": scatter_data,
            }

            print("[INFO] Scatter Data Loaded")

        except Exception as e:

            print("[SCATTER ERROR]", e)

    # =====================
    # 州销售 -> 地理气泡图
    # =====================

    if intent == "state":

        try:

            geo_data = query_state_geo_sales()

            queries["state_geo_map"] = {
                "view": "mv_state_sales",
                "sql": "state geo map",
                "data": geo_data,
            }

            print("[INFO] Geo Map Data Loaded")

        except Exception as e:

            print("[MAP ERROR]", e)

    # =====================
    # 支付分析 -> 热力图数据
    # =====================

    if intent == "payment":

        try:

            heatmap_data = query_payment_installment_matrix()

            queries["payment_installment_heatmap"] = {
                "view": "payments",
                "sql": """
                SELECT
                    payment_type,
                    payment_installments,
                    COUNT(*) AS transaction_count
                FROM payments
                GROUP BY
                    payment_type,
                    payment_installments
                """,
                "data": heatmap_data,
            }

            print("[INFO] Payment Heatmap Data Loaded")

        except Exception as e:

            print("[HEATMAP ERROR]", e)

    state = {
        "primary": {"data": result, "sql": sql, "view": view_name},
        "queries": queries,
        "forecast": forecast,
        "intent": {"label": intent, "confidence": 1.0},
    }

    return state


def query_payment_installment_matrix():
    sql = """
    SELECT
        payment_type,
        payment_installments,
        COUNT(*) AS transaction_count
    FROM payments
    WHERE payment_type IS NOT NULL
      AND payment_installments IS NOT NULL
    GROUP BY
        payment_type,
        payment_installments
    ORDER BY
        payment_type,
        payment_installments
    """

    return run_query(sql)


def query_weight_freight_scatter():

    sql = """
    SELECT
        p.product_weight_g,
        oi.freight_value,
        COUNT(*) AS order_count,
        o.order_status
    FROM order_items oi
    JOIN products p
        ON oi.product_id = p.product_id
    JOIN orders o
        ON oi.order_id = o.order_id
    WHERE
        p.product_weight_g IS NOT NULL
        AND oi.freight_value IS NOT NULL
    GROUP BY
        p.product_weight_g,
        oi.freight_value,
        o.order_status
    LIMIT 5000
    """

    return run_query(sql)


def query_review_texts():

    sql = """
    SELECT
        review_score,
        review_comment_message
    FROM order_reviews
    WHERE
        review_comment_message IS NOT NULL
        AND review_comment_message <> ''
    """

    return run_query(sql)


def query_state_geo_sales():

    sql = """
    SELECT
        s.customer_state,
        SUM(s.total_gmv) AS total_gmv,
        SUM(s.total_orders) AS total_orders
    FROM mv_state_sales s
    GROUP BY s.customer_state
    """

    return run_query(sql)
