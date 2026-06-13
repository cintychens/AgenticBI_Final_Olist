from utils.db import run_query
from agents.llm_agent import classify_question
from models.forecast_model import forecast_sales
from config.data_dictionary import DATA_DICTIONARY

PREAGGREGATED_VIEW_MAPPING = {
    "sales": "mv_monthly_sales",
    "state": "mv_state_sales",
    "category": "mv_category_sales",
    "delivery": "mv_delivery_perf",
    "payment": "mv_payment_dist",
    "seller": "mv_seller_perf",
}

VIEW_MAPPING = {
    **PREAGGREGATED_VIEW_MAPPING,
    "review": "order_reviews",
}

FALLBACK_BASE_TABLE = "orders"


def _format_preaggregated_view_catalog():
    catalog_lines = []

    for view_name, config in DATA_DICTIONARY["preaggregated_views"].items():
        fields = ", ".join(config.get("fields", []))
        preferred_for = "; ".join(config.get("preferred_for", []))
        catalog_lines.append(
            (
                f"- {view_name}: granularity={config.get('granularity')}; "
                f"fields={fields}; preferred_for={preferred_for}"
            )
        )

    return "\n".join(catalog_lines)


DATA_ANALYSIS_AGENT_QUERY_STRATEGY = f"""
Data Analysis Agent query policy:
1. Prefer pre-aggregated views whenever the user question matches an existing
   pre-computed business dimension.
2. Use the following view catalog as the source-of-truth configuration.
{_format_preaggregated_view_catalog()}
3. Only fall back to base tables when the requested dimension is not covered by
   the pre-aggregated views, such as raw review text, item-level freight/size
   analysis, or specific order-level detail.
"""


def get_preaggregated_view_config(view_name):
    return DATA_DICTIONARY["preaggregated_views"].get(view_name)


def get_query_source_for_intent(intent):
    return VIEW_MAPPING.get(intent)


def _query_source_type(source_name):
    if source_name in DATA_DICTIONARY["preaggregated_views"]:
        return "preaggregated_view"

    if source_name in DATA_DICTIONARY["base_tables"]:
        return "base_table"

    return "derived_base_table_query"


def _query_source_trace(intent, source_name):
    if not source_name:
        return (
            f"intent={intent}: no matching pre-aggregated view; "
            f"fallback={FALLBACK_BASE_TABLE}"
        )

    source_type = _query_source_type(source_name)

    if source_type == "preaggregated_view":
        config = get_preaggregated_view_config(source_name) or {}
        return (
            f"intent={intent}: hit pre-aggregated view {source_name} "
            f"(granularity={config.get('granularity')}, "
            f"fields={', '.join(config.get('fields', []))})"
        )

    return f"intent={intent}: fallback/query base source {source_name}"


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def _is_2017_question(question):
    return "2017" in str(question)


def _append_unique(items, item):
    if item not in items:
        items.append(item)


def detect_required_intents(question, primary_intent):
    text = str(question).lower()
    intents = []

    if primary_intent:
        _append_unique(intents, primary_intent)

    if _contains_any(text, ["全部分析", "全部结果", "整体运营", "三个月", "优先改进", "改进策略", "运营改进", "运营方案"]):
        for item in [
            "sales",
            "state",
            "delivery",
            "payment",
            "category",
            "seller",
            "review",
            "forecast",
        ]:
            _append_unique(intents, item)

    if _contains_any(text, ["gmv", "销售", "销售额", "月度", "按月", "趋势"]):
        _append_unique(intents, "sales")

    if _contains_any(text, ["州", "各州", "地区", "区域", "东北部"]):
        _append_unique(intents, "state")

    if _contains_any(text, ["准时", "交付", "配送", "延迟", "物流"]):
        _append_unique(intents, "delivery")

    if _contains_any(text, ["支付", "分期", "信用卡"]):
        _append_unique(intents, "payment")

    if _contains_any(text, ["卖家", "差评率", "评分最低"]):
        _append_unique(intents, "seller")

    if _contains_any(text, ["评论", "评价", "差评品类", "差评原因", "情感", "词云"]):
        _append_unique(intents, "review")

    if _contains_any(text, ["品类", "产品类别"]):
        _append_unique(intents, "category")

    if _contains_any(text, ["预测", "未来", "6周", "6 周"]):
        _append_unique(intents, "forecast")

    return intents or ["sales"]


def detect_required_intents(question, primary_intent):
    text = str(question).lower()
    intents = []

    asks_full_analysis = _contains_any(
        text,
        [
            "全部分析",
            "全部结果",
            "整体运营",
            "平台 3 个月",
            "平台3个月",
            "三大优先",
            "优先改进策略",
            "全局分析",
        ],
    )

    asks_northeast_return_plan = _contains_any(
        text,
        [
            "东北部",
            "巴西东北",
            "高退货",
            "退货率",
            "运营改进方案",
            "具体的运营改进",
        ],
    )

    if asks_full_analysis and not asks_northeast_return_plan:
        return [
            "sales",
            "state",
            "delivery",
            "payment",
            "category",
            "seller",
            "review",
            "forecast",
        ]

    if asks_northeast_return_plan:
        return [
            "state",
            "delivery",
            "seller",
            "review",
        ]

    asks_monthly_sales = _contains_any(
        text,
        ["gmv", "按月", "月度", "趋势", "销售趋势", "monthly"],
    )
    asks_state_sales = _contains_any(
        text,
        ["州", "各州", "哪个州", "州的销售", "地区", "区域", "state"],
    )
    asks_delivery = _contains_any(
        text,
        ["准时", "交付", "配送", "延迟", "物流", "delivery"],
    )
    asks_payment = _contains_any(
        text,
        ["支付", "分期", "信用卡", "payment", "installment"],
    )
    asks_seller = _contains_any(
        text,
        ["卖家", "差评率", "评分最低", "seller"],
    )
    asks_review = _contains_any(
        text,
        ["评论", "评价", "差评品类", "差评原因", "情感", "词云", "review"],
    )
    asks_category = _contains_any(
        text,
        ["品类", "产品类别", "category"],
    )
    asks_forecast = _contains_any(
        text,
        ["预测", "未来", "6周", "6 周", "forecast"],
    )
    asks_weight_freight = _contains_any(
        text,
        ["重量", "尺寸", "运费", "freight", "weight"],
    )

    if asks_forecast:
        _append_unique(intents, "forecast")

    if asks_monthly_sales:
        _append_unique(intents, "sales")

    if asks_state_sales:
        _append_unique(intents, "state")

    if asks_delivery or asks_weight_freight:
        _append_unique(intents, "delivery")

    if asks_payment:
        _append_unique(intents, "payment")

    if asks_category:
        _append_unique(intents, "category")

    if asks_seller:
        _append_unique(intents, "seller")

    if asks_review:
        _append_unique(intents, "review")

    if not intents and primary_intent:
        _append_unique(intents, primary_intent)

    return intents or ["sales"]


def select_best_view(question):

    intent = classify_question(question)
    required_intents = detect_required_intents(question, intent)

    print(f"[LLM INTENT] {intent}")
    print(f"[REQUIRED INTENTS] {required_intents}")

    return VIEW_MAPPING.get(intent)


def generate_sql(view_name, question):

    if view_name == "mv_monthly_sales":

        year_filter = "WHERE LEFT(ym, 4) = '2017'" if _is_2017_question(question) else ""

        return f"""
        SELECT
            ym,
            total_gmv,
            total_orders,
            avg_basket
        FROM mv_monthly_sales
        {year_filter}
        ORDER BY ym
        """

    elif view_name == "mv_state_sales":

        year_filter = "WHERE LEFT(ym, 4) = '2017'" if _is_2017_question(question) else ""

        return f"""
        SELECT
            customer_state,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders,
            ROUND(SUM(total_gmv) / NULLIF(SUM(total_orders), 0), 2) AS avg_basket
        FROM mv_state_sales
        {year_filter}
        GROUP BY customer_state
        ORDER BY total_gmv DESC
        LIMIT 10
        """

    elif view_name == "mv_category_sales":

        year_filter = "AND LEFT(ym, 4) = '2017'" if _is_2017_question(question) else ""

        return f"""
        SELECT
            product_category,
            SUM(total_gmv) AS total_gmv,
            SUM(total_orders) AS total_orders,
            AVG(avg_price) AS avg_price
        FROM mv_category_sales
        WHERE product_category IS NOT NULL
        {year_filter}
        GROUP BY product_category
        ORDER BY total_gmv DESC
        LIMIT 10
        """

    elif view_name == "mv_delivery_perf":

        year_filter = "WHERE LEFT(ym, 4) = '2017'" if _is_2017_question(question) else ""

        return f"""
        SELECT
            customer_state,
            ROUND(AVG(avg_delivery_days), 2) AS avg_delivery_days,
            ROUND(AVG(on_time_rate), 4) AS on_time_rate,
            SUM(delayed_orders) AS delayed_orders
        FROM mv_delivery_perf
        {year_filter}
        GROUP BY customer_state
        ORDER BY avg_delivery_days DESC
        LIMIT 10
        """

    elif view_name == "mv_payment_dist":

        year_filter = "WHERE LEFT(ym, 4) = '2017'" if _is_2017_question(question) else ""

        return f"""
        SELECT
            payment_type,
            SUM(total_transactions) AS total_transactions,
            ROUND(AVG(avg_installments), 2) AS avg_installments,
            SUM(total_value) AS total_value
        FROM mv_payment_dist
        {year_filter}
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
    required_intents = detect_required_intents(question, intent)
    query_strategy_trace = []

    print(f"[LLM INTENT] {intent}")
    print(f"[REQUIRED INTENTS] {required_intents}")

    forecast = None

    if intent == "forecast":

        sql = generate_sql("mv_monthly_sales", question)

        result = run_query(sql)

        forecast = forecast_sales()

        view_name = "mv_monthly_sales"
        query_strategy_trace.append(_query_source_trace(intent, view_name))

        print("[INFO] Forecast Agent triggered")

    else:

        view_name = get_query_source_for_intent(intent)
        query_strategy_trace.append(_query_source_trace(intent, view_name))

        print(f"[VIEW] {view_name}")

        if view_name:

            sql = generate_sql(view_name, question)

            print(f"[INFO] Using View: {view_name}")

        else:

            sql = f"""
            SELECT *
            FROM {FALLBACK_BASE_TABLE}
            LIMIT 10
            """

            print("[INFO] Fallback to Base Table")

        result = run_query(sql)

    # =====================
    # 多图表查询集合
    # =====================

    queries = {
        "main_query": {
            "view": view_name,
            "sql": sql,
            "data": result,
            "intent": intent,
            "source_type": _query_source_type(view_name),
            "view_config": get_preaggregated_view_config(view_name),
        }
    }

    for extra_intent in required_intents:

        if extra_intent == intent:
            continue

        if extra_intent == "forecast":

            extra_view = "mv_monthly_sales"
            extra_sql = generate_sql(extra_view, question)
            extra_result = run_query(extra_sql)
            forecast = forecast_sales()
            query_strategy_trace.append(_query_source_trace(extra_intent, extra_view))

            print("[INFO] Extra Forecast Agent triggered")

        else:

            extra_view = get_query_source_for_intent(extra_intent)

            if not extra_view:
                query_strategy_trace.append(
                    _query_source_trace(extra_intent, extra_view)
                )
                continue

            extra_sql = generate_sql(extra_view, question)
            extra_result = run_query(extra_sql)
            query_strategy_trace.append(_query_source_trace(extra_intent, extra_view))

            print(f"[INFO] Extra View Loaded: {extra_view}")

        queries[f"{extra_intent}_query"] = {
            "view": extra_view,
            "sql": extra_sql,
            "data": extra_result,
            "intent": extra_intent,
            "source_type": _query_source_type(extra_view),
            "view_config": get_preaggregated_view_config(extra_view),
        }

    # =====================
    # 评论分析 -> 词云数据
    # =====================
    if "review" in required_intents:

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

        negative_category_data = query_top_negative_categories()

        queries["top_negative_categories"] = {
            "view": "orders+order_items+products+order_reviews",
            "sql": "top 10 negative review categories",
            "data": negative_category_data,
        }

        print("[INFO] Positive WordCloud Loaded")

        print("[INFO] Negative WordCloud Loaded")

        print("[INFO] Top Negative Categories Loaded")

    # =====================
    # 配送分析 -> 重量运费散点图
    # =====================

    asks_weight_freight_chart = _contains_any(
        str(question).lower(),
        ["重量", "尺寸", "运费", "freight", "weight", "size"],
    )

    if "delivery" in required_intents and asks_weight_freight_chart:

        try:

            scatter_data = query_weight_freight_scatter()

            queries["weight_freight_scatter"] = {
                "view": "products+order_items+orders",
                "sql": """
                weight vs freight scatter
                """,
                "data": scatter_data,
            }

            dimension_data = query_dimension_freight_analysis()

            queries["dimension_freight_analysis"] = {
                "view": "products+order_items",
                "sql": "dimension and freight analysis",
                "data": dimension_data,
            }

            print("[INFO] Scatter Data Loaded")

            print("[INFO] Dimension Freight Data Loaded")

        except Exception as e:

            print("[SCATTER ERROR]", e)

    # =====================
    # 州销售 -> 地理气泡图
    # =====================

    question_text = str(question).lower()
    is_global_analysis = _contains_any(
        question_text,
        ["全部分析", "全部结果", "整体运营", "优先改进", "改进策略"],
    )
    asks_geo_map = _contains_any(
        question_text,
        ["地图", "地理", "分布", "气泡图", "热力图", "map", "geo"],
    )
    asks_anomaly = _contains_any(
        question_text,
        [
            "异常",
            "预警",
            "波动",
            "突降",
            "骤降",
            "突升",
            "自动扫描",
            "anomaly",
        ],
    )

    if "state" in required_intents:

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

    asks_installment_chart = _contains_any(
        str(question).lower(),
        ["分期", "installment", "installments"],
    )

    if "payment" in required_intents:

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

    # =====================
    # Sales / forecast anomaly detection
    # =====================

    if asks_anomaly or is_global_analysis:

        try:

            anomaly_data = query_sales_anomalies()

            queries["sales_anomaly_detection"] = {
                "view": "mv_monthly_sales",
                "sql": "monthly sales anomaly detection",
                "data": anomaly_data,
            }

            state_drop_data = query_state_order_drop_anomalies()

            queries["state_order_drop_anomaly"] = {
                "view": "mv_state_sales",
                "sql": "state order drop anomaly detection",
                "data": state_drop_data,
            }

            review_spike_data = query_review_spike_anomalies()

            queries["review_rate_spike_anomaly"] = {
                "view": "orders+order_reviews",
                "sql": "negative review rate spike anomaly detection",
                "data": review_spike_data,
            }

            print("[INFO] Sales Anomaly Data Loaded")
            print("[INFO] State Order Drop Anomaly Data Loaded")
            print("[INFO] Review Rate Spike Anomaly Data Loaded")

        except Exception as e:

            print("[ANOMALY ERROR]", e)

    if _contains_any(str(question).lower(), ["东北部", "退货", "取消", "return", "refund"]):

        try:

            northeast_risk_data = query_northeast_order_risk()

            queries["northeast_return_risk"] = {
                "view": "orders+customers",
                "sql": "northeast cancellation and return-risk proxy",
                "data": northeast_risk_data,
            }

            print("[INFO] Northeast Risk Data Loaded")

        except Exception as e:

            print("[NORTHEAST RISK ERROR]", e)

    state = {
        "primary": {"data": result, "sql": sql, "view": view_name},
        "queries": queries,
        "forecast": forecast,
        "intent": {
            "label": intent,
            "confidence": 1.0,
            "required_intents": required_intents,
        },
        "query_strategy": {
            "policy": DATA_ANALYSIS_AGENT_QUERY_STRATEGY,
            "trace": query_strategy_trace,
        },
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


def query_dimension_freight_analysis():

    sql = """
    SELECT
        COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
        ROUND(AVG(p.product_weight_g), 2) AS avg_weight_g,
        ROUND(AVG(
            p.product_length_cm *
            p.product_height_cm *
            p.product_width_cm
        ), 2) AS avg_volume_cm3,
        ROUND(AVG(oi.freight_value), 2) AS avg_freight_value,
        COUNT(*) AS order_count
    FROM order_items oi
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    WHERE
        p.product_weight_g IS NOT NULL
        AND p.product_length_cm IS NOT NULL
        AND p.product_height_cm IS NOT NULL
        AND p.product_width_cm IS NOT NULL
        AND oi.freight_value IS NOT NULL
    GROUP BY product_category
    HAVING order_count >= 30
    ORDER BY avg_freight_value DESC
    LIMIT 20
    """

    return run_query(sql)


def query_top_negative_categories():

    sql = """
    SELECT
        COALESCE(t.product_category_name_english, p.product_category_name) AS product_category,
        COUNT(*) AS negative_review_count,
        ROUND(AVG(r.review_score), 2) AS avg_review_score,
        GROUP_CONCAT(
            LEFT(r.review_comment_message, 120)
            SEPARATOR ' | '
        ) AS sample_comments
    FROM order_reviews r
    JOIN orders o
        ON r.order_id = o.order_id
    JOIN order_items oi
        ON o.order_id = oi.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    LEFT JOIN product_category_name_translation t
        ON p.product_category_name = t.product_category_name
    WHERE
        r.review_score <= 2
        AND r.review_comment_message IS NOT NULL
        AND r.review_comment_message <> ''
        AND p.product_category_name IS NOT NULL
    GROUP BY product_category
    ORDER BY negative_review_count DESC
    LIMIT 10
    """

    return run_query(sql)


def query_sales_anomalies():

    sql = """
    SELECT
        ym,
        total_gmv,
        total_orders,
        avg_basket
    FROM mv_monthly_sales
    ORDER BY ym
    """

    df = run_query(sql)

    if df is None or df.empty:
        return df

    df = df.copy()
    historical_window = df["total_gmv"].rolling(
        window=3,
        min_periods=2,
    )

    df["rolling_avg_gmv"] = historical_window.mean().shift(1)
    df["rolling_std_gmv"] = historical_window.std().shift(1)
    df["anomaly_score"] = 0.0

    valid_std = (
        df["rolling_std_gmv"].notna()
        & (df["rolling_std_gmv"] > 0)
    )
    df.loc[valid_std, "anomaly_score"] = (
        (
            df.loc[valid_std, "total_gmv"]
            - df.loc[valid_std, "rolling_avg_gmv"]
        )
        / df.loc[valid_std, "rolling_std_gmv"]
    )
    df["anomaly_type"] = "normal"
    df.loc[df["anomaly_score"] >= 2.0, "anomaly_type"] = "positive_spike"
    df.loc[df["anomaly_score"] <= -2.0, "anomaly_type"] = "negative_drop"

    return df


def query_state_order_drop_anomalies():

    sql = """
    SELECT
        ym,
        customer_state,
        SUM(total_orders) AS total_orders
    FROM mv_state_sales
    GROUP BY
        ym,
        customer_state
    ORDER BY
        customer_state,
        ym
    """

    df = run_query(sql)

    if df is None or df.empty:
        return df

    df = df.copy()
    df["previous_orders"] = (
        df.groupby("customer_state")["total_orders"].shift(1)
    )
    df["order_change_rate"] = (
        (df["total_orders"] - df["previous_orders"])
        / df["previous_orders"]
    )
    df["anomaly_type"] = "normal"
    df.loc[
        (df["previous_orders"] >= 30)
        & (df["order_change_rate"] <= -0.35),
        "anomaly_type",
    ] = "state_order_drop"

    return df


def query_review_spike_anomalies():

    sql = """
    SELECT
        DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m') AS ym,
        COUNT(*) AS review_count,
        SUM(
            CASE
                WHEN r.review_score <= 2 THEN 1
                ELSE 0
            END
        ) AS negative_reviews,
        SUM(
            CASE
                WHEN r.review_score <= 2 THEN 1
                ELSE 0
            END
        ) / COUNT(*) AS negative_review_rate
    FROM order_reviews r
    JOIN orders o
        ON r.order_id = o.order_id
    WHERE o.order_purchase_timestamp IS NOT NULL
    GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%%Y-%%m')
    ORDER BY ym
    """

    df = run_query(sql)

    if df is None or df.empty:
        return df

    df = df.copy()
    df["previous_negative_rate"] = df["negative_review_rate"].shift(1)
    df["rate_change"] = (
        df["negative_review_rate"]
        - df["previous_negative_rate"]
    )
    df["anomaly_type"] = "normal"
    df.loc[
        (df["review_count"] >= 100)
        & (df["rate_change"] >= 0.08),
        "anomaly_type",
    ] = "negative_review_rate_spike"

    return df


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
        SUM(s.total_orders) AS total_orders,
        g.lat,
        g.lon
    FROM mv_state_sales s
    LEFT JOIN (
        SELECT
            geolocation_state AS customer_state,
            AVG(geolocation_lat) AS lat,
            AVG(geolocation_lng) AS lon
        FROM geolocation
        WHERE geolocation_state IS NOT NULL
        GROUP BY geolocation_state
    ) g
        ON s.customer_state = g.customer_state
    GROUP BY s.customer_state, g.lat, g.lon
    """

    return run_query(sql)


def query_northeast_order_risk():

    sql = """
    SELECT
        c.customer_state,
        COUNT(*) AS total_orders,
        SUM(
            CASE
                WHEN o.order_status IN ('canceled', 'unavailable')
                THEN 1
                ELSE 0
            END
        ) AS risk_orders,
        ROUND(
            SUM(
                CASE
                    WHEN o.order_status IN ('canceled', 'unavailable')
                    THEN 1
                    ELSE 0
                END
            ) / COUNT(*),
            4
        ) AS risk_rate,
        ROUND(
            AVG(
                CASE
                    WHEN o.order_delivered_customer_date IS NOT NULL
                    THEN DATEDIFF(
                        o.order_delivered_customer_date,
                        o.order_purchase_timestamp
                    )
                    ELSE NULL
                END
            ),
            2
        ) AS avg_delivery_days
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE c.customer_state IN (
        'AL', 'BA', 'CE', 'MA', 'PB',
        'PE', 'PI', 'RN', 'SE'
    )
    GROUP BY c.customer_state
    ORDER BY risk_rate DESC, avg_delivery_days DESC
    """

    return run_query(sql)
