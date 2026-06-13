from agents.llm_agent import client
from config.settings import MODEL_NAME


INTERNAL_LABELS = {
    "main_query": "主查询",
    "sales_query": "销售查询",
    "state_query": "州销售查询",
    "category_query": "品类查询",
    "delivery_query": "配送查询",
    "payment_query": "支付查询",
    "seller_query": "卖家查询",
    "review_query": "评论查询",
    "forecast_query": "预测查询",
    "northeast_return_risk": "东北部履约风险查询",
}


def _display_query_name(name):
    return INTERNAL_LABELS.get(name, name)


FIELD_DISPLAY_NAMES = {
    "ym": "年月",
    "ds": "日期",
    "y": "历史销售额",
    "yhat": "预测销售额",
    "yhat_lower": "预测下限",
    "yhat_upper": "预测上限",
    "is_forecast": "是否预测值",
    "total_gmv": "总GMV",
    "total_orders": "订单量",
    "avg_basket": "平均客单价",
    "total_freight": "总运费",
    "customer_state": "客户州",
    "seller_state": "卖家州",
    "product_category": "商品品类",
    "payment_type": "支付方式",
    "payment_installments": "分期数",
    "total_transactions": "交易次数",
    "avg_installments": "平均分期数",
    "total_value": "支付总额",
    "avg_delivery_days": "平均配送天数",
    "on_time_rate": "准时交付率",
    "delayed_orders": "延迟订单量",
    "seller_id": "卖家ID",
    "avg_review_score": "平均评分",
    "review_score": "评论评分",
    "review_count": "评论数",
    "negative_reviews": "差评数",
    "negative_review_count": "差评数",
    "negative_review_rate": "差评率",
    "rate_change": "差评率变化",
    "previous_orders": "上一期订单量",
    "order_change_rate": "订单量变化率",
    "anomaly_type": "异常类型",
    "risk_rate": "风险率",
    "risk_orders": "风险订单数",
    "product_weight_g": "商品重量(g)",
    "product_length_cm": "商品长度(cm)",
    "product_height_cm": "商品高度(cm)",
    "product_width_cm": "商品宽度(cm)",
    "freight_value": "运费",
    "avg_freight_value": "平均运费",
    "avg_volume_cm3": "平均体积(cm3)",
    "order_count": "订单数",
    "order_status": "订单状态",
    "unique_customers": "独立客户数",
}


def _display_field_name(name):
    return FIELD_DISPLAY_NAMES.get(name, name)


def _translate_record_keys(record):
    return {_display_field_name(key): value for key, value in record.items()}


def _format_records(df, max_rows=5):
    if df is None or df.empty:
        return "无数据"

    rows = [_translate_record_keys(row) for row in df.head(max_rows).to_dict("records")]
    return str(rows)


def _summarize_dataframe(name, payload):
    df = payload.get("data")
    view_name = payload.get("view", "")
    intent = payload.get("intent", "")
    display_name = _display_query_name(name)

    if df is None or df.empty:
        return f"{display_name}: view={view_name}, intent={intent}, 未返回数据。"

    numeric_summary = {}
    for column in df.columns:
        try:
            series = df[column]
            if series.dtype.kind in "if":
                numeric_summary[_display_field_name(column)] = {
                    "sum": round(float(series.sum()), 2),
                    "mean": round(float(series.mean()), 2),
                    "max": round(float(series.max()), 2),
                    "min": round(float(series.min()), 2),
                }
        except Exception:
            continue

    return "\n".join(
        [
            f"{display_name}:",
            f"- 数据来源: {view_name}",
            f"- 分析意图: {intent}",
            f"- 数据规模: {df.shape[0]} 行 x {df.shape[1]} 列",
            f"- 字段: {[_display_field_name(column) for column in df.columns]}",
            f"- 数值摘要: {numeric_summary}",
            f"- 样例记录: {_format_records(df)}",
        ]
    )


def _summarize_forecast(forecast):
    if forecast is None or forecast.empty:
        return "无预测结果。"

    future = forecast[forecast["is_forecast"] == True]
    if future.empty:
        return "预测对象存在，但没有未来预测行。"

    return "\n".join(
        [
            "预测摘要:",
            f"- 未来预测周期数: {len(future)}",
            f"- 未来平均预测销售额: {future['yhat'].mean():,.2f}",
            f"- 未来最高预测销售额: {future['yhat'].max():,.2f}",
            f"- 未来最低预测销售额: {future['yhat'].min():,.2f}",
            f"- 第一条未来预测记录: {future.head(1).to_dict('records')}",
        ]
    )


def _fallback_answer(state):
    advice = state.get("advice_detail", {})
    highlights = advice.get("highlights", []) if isinstance(advice, dict) else []
    recommendations = advice.get("recommendations", []) if isinstance(advice, dict) else []

    text = []
    if highlights:
        text.append("核心结论：")
        text.extend(f"- {item}" for item in highlights[:4])

    if recommendations:
        text.append("\n建议：")
        text.extend(f"- {item}" for item in recommendations[:4])

    return "\n".join(text) or "本轮分析已完成，右侧已展示对应图表和指标。"


def generate_narrative_answer(question, state):
    queries = state.get("queries", {})
    query_summaries = [
        _summarize_dataframe(name, payload)
        for name, payload in queries.items()
    ]

    review_insights = state.get("review_insights", {}) or {}
    what_if = state.get("what_if")
    forecast = state.get("forecast")
    advice_detail = state.get("advice_detail", {})

    prompt = f"""
你是 Agentic BI 系统中的最终回答 Agent。
请基于用户问题、SQL 查询结果摘要、预测结果、评论洞察和决策建议，生成自然、专业、具体的中文回答。

用户问题：
{question}

查询结果摘要：
{chr(10).join(query_summaries)}

预测结果：
{_summarize_forecast(forecast)}

评论洞察：
{review_insights}

What-if 结果：
{what_if}

规则/LLM 决策建议：
{advice_detail}

回答要求：
1. 直接回答用户的问题，不要只说“已完成分析”。
2. 如果问题问数值，必须给出关键数值。
3. 如果问题问趋势，解释上升、下降、峰值或区域差异。
4. 如果问题问原因，给出基于数据的可能原因。
5. 如果问题问策略，给出 3 条优先行动，必须可执行。
6. 数据库查询返回的原始取值必须保持原样，不要翻译、改写或本地化。例如 credit_card、boleto、SP、seller_id、product_category、评论关键词和评论原文都按数据里的原始写法输出。
7. 不要把 main_query、delivery_query、seller_query 这类内部查询标签写进最终回答正文。
8. 面向业务用户解释字段或指标时，必须使用中文名称，例如 total_gmv 写成“总GMV”，total_orders 写成“订单量”，avg_review_score 写成“平均评分”。
9. 只有 AI 自己生成的标题、解释、原因归纳、风险判断和运营建议必须使用中文。
10. 如果输入摘要里有英文规则句，请转写成自然中文；但其中来自数据库的原始字段值和原始文本必须保持不变。
11. 结构清晰，长度控制在 250 到 500 字。
12. 不要编造没有出现在数据摘要里的具体数值。
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名资深电商 BI 分析师，擅长把数据库结果转成清晰的中文业务结论。"
                        "数据库查询返回的原始取值必须保持原样，包括州缩写、支付类型、"
                        "seller_id、品类名、评论关键词和评论原文。"
                        "面向业务用户解释字段或指标时使用中文名称，"
                        "只有你自己生成的解释、结论、原因归纳和运营建议必须使用中文，"
                        "不要输出英文解释或内部查询标签。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=900,
        )

        answer = response.choices[0].message.content.strip()
        if answer:
            return answer

    except Exception as exc:
        print("[NARRATIVE ANSWER ERROR]", exc)

    return _fallback_answer(state)
