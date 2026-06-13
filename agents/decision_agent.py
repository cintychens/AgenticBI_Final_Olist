from agents.llm_agent import generate_business_advice


QUERY_DISPLAY_NAMES = {
    "sales_query": "销售分析",
    "state_query": "州销售分析",
    "category_query": "品类销售分析",
    "delivery_query": "配送表现分析",
    "payment_query": "支付方式分析",
    "seller_query": "卖家评分分析",
    "review_query": "评论洞察分析",
    "forecast_query": "销售预测分析",
    "sales_anomaly_detection": "月度GMV异常检测",
    "state_order_drop_anomaly": "州级订单量骤降检测",
    "review_rate_spike_anomaly": "差评率突升检测",
    "northeast_return_risk": "巴西东北部履约风险分析",
    "top_negative_categories": "差评品类原因分析",
    "weight_freight_scatter": "重量与运费关系分析",
    "dimension_freight_analysis": "尺寸与运费关系分析",
    "payment_installment_heatmap": "支付分期分析",
    "state_geo_map": "州销售地图分析",
}


def _display_query_name(query_name):
    return QUERY_DISPLAY_NAMES.get(query_name, query_name.replace("_", " "))


def generate_advice(state):

    df = state.get("primary", {}).get("data")
    queries = state.get("queries", {})
    review_insights = state.get("review_insights", {})
    forecast = state.get("forecast")

    highlights = []
    recommendations = []

    llm_advice = None

    if df is None or df.empty:
        return {
            "highlights": ["当前查询未返回有效数据。"],
            "recommendations": [
                "建议检查数据库连接、SQL查询条件或换一个更明确的业务问题。"
            ],
        }

    # =====================
    # GMV分析
    # =====================
    if "total_gmv" in df.columns:

        total_gmv = df["total_gmv"].sum()

        highlights.append(f"当前查询结果的总GMV为 {total_gmv:,.2f}。")

        if total_gmv > 10000000:

            recommendations.append(
                f"GMV达到 {total_gmv / 1000000:.2f} 百万，销售规模较大，建议增加高销量品类库存并加强营销投入。"
            )

        elif total_gmv > 5000000:

            recommendations.append("当前销售表现良好，建议持续关注核心品类和重点地区。")

        else:

            recommendations.append("销售规模相对较小，建议挖掘高潜力市场并提升转化率。")

    # =====================
    # 订单量分析
    # =====================
    if "total_orders" in df.columns:

        total_orders = df["total_orders"].sum()

        highlights.append(f"当前查询结果共包含 {total_orders:,.0f} 个订单。")

        if total_orders > 80000:

            recommendations.append("订单量接近10万单，建议重点关注仓储容量和配送能力。")

        elif total_orders > 30000:

            recommendations.append("订单规模稳定，建议持续优化订单履约效率。")

        else:

            recommendations.append("订单量较低，建议通过促销活动提升用户下单频率。")

    # =====================
    # 客单价分析
    # =====================
    if "avg_basket" in df.columns:

        avg_basket = df["avg_basket"].mean()

        highlights.append(f"平均客单价为 {avg_basket:.2f} 元。")

        if avg_basket > 120:

            recommendations.append("客单价较高，建议推广高价值商品和组合销售策略。")

        elif avg_basket > 80:

            recommendations.append("客单价处于正常水平，可通过关联销售提升订单价值。")

        else:

            recommendations.append("客单价偏低，建议推出满减活动提高用户单次消费金额。")

    # =====================
    # 配送准时率分析
    # =====================
    if "on_time_rate" in df.columns:

        avg_rate = df["on_time_rate"].mean()
        display_rate = avg_rate / 100 if avg_rate > 1 else avg_rate

        highlights.append(f"当前平均准时率为 {display_rate:.2%}。")

        if display_rate < 0.80:

            recommendations.append("准时率偏低，建议重点优化物流履约流程。")

        elif display_rate < 0.90:

            recommendations.append("准时率处于正常水平，建议持续监控重点区域物流表现。")

        else:

            recommendations.append("准时率表现优秀，可作为物流运营优势进行宣传。")

    # =====================
    # 配送时长分析
    # =====================
    if "avg_delivery_days" in df.columns and "customer_state" in df.columns:

        worst = df.sort_values(by="avg_delivery_days", ascending=False).iloc[0]

        highlights.append(f"{worst['customer_state']} 的平均配送时间最高。")

        recommendations.append("建议检查该地区的仓储覆盖、承运商能力和卖家发货效率。")

    # =====================
    # 支付方式分析
    # =====================
    if "payment_type" in df.columns and "total_transactions" in df.columns:

        top_payment = df.sort_values(by="total_transactions", ascending=False).iloc[0]

        highlights.append(f"最常用的支付方式是 {top_payment['payment_type']}。")

        recommendations.append(
            f"建议围绕 {top_payment['payment_type']} 优化支付体验，并设计针对性的营销活动。"
        )

    # =====================
    # 卖家绩效分析
    # =====================
    if "avg_review_score" in df.columns and "seller_id" in df.columns:

        low_seller = df.sort_values(by="avg_review_score", ascending=True).iloc[0]

        highlights.append(f"卖家 {low_seller['seller_id']} 的评分较低。")

        recommendations.append(
            "建议将该卖家列入重点监控名单，分析差评原因并制定整改措施。"
        )

    for query_name, payload in queries.items():

        if query_name == "main_query":
            continue

        display_query_name = _display_query_name(query_name)

        query_df = payload.get("data")

        if query_df is None or query_df.empty:
            continue

        if "ym" in query_df.columns and "total_gmv" in query_df.columns:

            period_gmv = query_df["total_gmv"].sum()

            highlights.append(
                f"{display_query_name}的总GMV为 {period_gmv:,.2f}。"
            )

        if "customer_state" in query_df.columns and "total_gmv" in query_df.columns:

            top_state = query_df.sort_values(
                by="total_gmv",
                ascending=False,
            ).iloc[0]

            highlights.append(
                f"{display_query_name}中销售额最高的州是 {top_state['customer_state']}，"
                f"GMV为 {top_state['total_gmv']:,.2f}。"
            )

        if (
            "customer_state" in query_df.columns
            and "avg_delivery_days" in query_df.columns
            and "on_time_rate" in query_df.columns
        ):

            avg_rate = query_df["on_time_rate"].mean()
            display_rate = avg_rate / 100 if avg_rate > 1 else avg_rate
            worst_state = query_df.sort_values(
                by="avg_delivery_days",
                ascending=False,
            ).iloc[0]

            highlights.append(
                f"{display_query_name}的平均准时交付率为 {display_rate:.2%}；"
                f"{worst_state['customer_state']} 的平均配送时长最高。"
            )

            recommendations.append(
                "针对配送延迟较严重的州，建议检查仓储覆盖、承运商路线、"
                "卖家发货效率以及承诺送达时间是否过于乐观。"
            )

        if "payment_type" in query_df.columns and "total_transactions" in query_df.columns:

            top_payment = query_df.sort_values(
                by="total_transactions",
                ascending=False,
            ).iloc[0]

            avg_installments = query_df["avg_installments"].mean()

            highlights.append(
                f"{display_query_name}中最受欢迎的支付方式是 "
                f"{top_payment['payment_type']}；平均分期数为 "
                f"{avg_installments:.2f}。"
            )

        if "seller_id" in query_df.columns and "avg_review_score" in query_df.columns:

            low_seller = query_df.sort_values(
                by="avg_review_score",
                ascending=True,
            ).iloc[0]

            highlights.append(
                f"{display_query_name}中评分最低的卖家是 {low_seller['seller_id']}，"
                f"平均评分为 {low_seller['avg_review_score']:.2f}。"
            )

        if (
            "customer_state" in query_df.columns
            and "risk_rate" in query_df.columns
            and "risk_orders" in query_df.columns
        ):

            highest_risk = query_df.sort_values(
                by="risk_rate",
                ascending=False,
            ).iloc[0]

            highlights.append(
                "东北部履约风险分析显示："
                f"{highest_risk['customer_state']} 的取消/退货风险代理指标最高，"
                f"风险率为 {highest_risk['risk_rate']:.2%}。"
            )

            recommendations.extend(
                [
                    "针对巴西东北部，优先复核承运商SLA，并为高风险州增加备用承运商。",
                    "建立服务东北部高风险州的卖家质量观察名单，重点跟踪低评分和高取消风险卖家。",
                    "通过提高预计送达时间准确性、加强包装质检和售后跟进，降低可预防的退货与取消风险。",
                ]
            )

    state_sources = [
        payload.get("data")
        for payload in queries.values()
        if payload.get("data") is not None
        and "customer_state" in payload.get("data").columns
        and "total_gmv" in payload.get("data").columns
    ]
    delivery_sources = [
        payload.get("data")
        for payload in queries.values()
        if payload.get("data") is not None
        and "customer_state" in payload.get("data").columns
        and "on_time_rate" in payload.get("data").columns
    ]
    payment_sources = [
        payload.get("data")
        for payload in queries.values()
        if payload.get("data") is not None
        and "payment_type" in payload.get("data").columns
        and "total_transactions" in payload.get("data").columns
    ]

    if state_sources and delivery_sources and payment_sources:

        state_df = state_sources[0]
        delivery_df = delivery_sources[0]
        payment_df = payment_sources[0]

        top_state = state_df.sort_values(
            by="total_gmv",
            ascending=False,
        ).iloc[0]
        top_payment = payment_df.sort_values(
            by="total_transactions",
            ascending=False,
        ).iloc[0]
        delivery_match = delivery_df[
            delivery_df["customer_state"] == top_state["customer_state"]
        ]

        if not delivery_match.empty:
            top_state_rate = delivery_match.iloc[0]["on_time_rate"]
            top_state_rate = top_state_rate / 100 if top_state_rate > 1 else top_state_rate

            highlights.append(
                f"综合回答：销售额最高的州是 {top_state['customer_state']}，"
                f"GMV为 {top_state['total_gmv']:,.2f}；该州准时交付率为 "
                f"{top_state_rate:.2%}；平台最受欢迎的支付方式是 "
                f"{top_payment['payment_type']}。"
            )

    # =====================
    # 评论分析
    # =====================
    if review_insights and review_insights.get("summary"):

        highlights.append(review_insights["summary"])

    negative_categories = review_insights.get("negative_categories", [])

    if negative_categories:

        worst_category = negative_categories[0]

        highlights.append(
            "差评最多的品类是 "
            f"{worst_category['product_category']}，"
            f"差评数量为 {worst_category['negative_review_count']}。"
        )

        recommendations.append(
            "建议优先对差评最多的品类做根因复盘，重点检查物流延迟、商品破损和售后处理效率。"
        )

    anomaly_payload = queries.get("sales_anomaly_detection", {})
    anomaly_df = anomaly_payload.get("data")

    if anomaly_df is not None and not anomaly_df.empty:

        anomalies = anomaly_df[anomaly_df["anomaly_type"] != "normal"]

        if not anomalies.empty:

            latest_anomaly = anomalies.iloc[-1]

            highlights.append(
                "检测到月度GMV异常："
                f"{latest_anomaly['ym']} 出现 {latest_anomaly['anomaly_type']}，"
                f"异常分数为 {latest_anomaly['anomaly_score']:.2f}。"
            )

            recommendations.append(
                "建议针对GMV异常月份复核营销活动日历、库存可用性、配送承载能力和数据质量。"
            )

    state_drop_payload = queries.get("state_order_drop_anomaly", {})
    state_drop_df = state_drop_payload.get("data")

    if state_drop_df is not None and not state_drop_df.empty:

        state_drop_anomalies = state_drop_df[
            state_drop_df["anomaly_type"] != "normal"
        ]

        if not state_drop_anomalies.empty:

            worst_drop = state_drop_anomalies.sort_values(
                by="order_change_rate",
                ascending=True,
            ).iloc[0]

            highlights.append(
                "检测到州级订单量骤降："
                f"{worst_drop['customer_state']} 在 {worst_drop['ym']} "
                f"订单环比变化为 {worst_drop['order_change_rate']:.2%}。"
            )

            recommendations.append(
                "建议针对订单骤降州复核该月营销活动、库存可用性、配送异常、"
                "卖家供给变化和数据采集质量。"
            )

    review_spike_payload = queries.get("review_rate_spike_anomaly", {})
    review_spike_df = review_spike_payload.get("data")

    if review_spike_df is not None and not review_spike_df.empty:

        review_spike_anomalies = review_spike_df[
            review_spike_df["anomaly_type"] != "normal"
        ]

        if not review_spike_anomalies.empty:

            latest_spike = review_spike_anomalies.iloc[-1]

            highlights.append(
                "检测到差评率突升："
                f"{latest_spike['ym']} 负向评论率为 "
                f"{latest_spike['negative_review_rate']:.2%}，"
                f"较上一期上升 {latest_spike['rate_change']:.2%}。"
            )

            recommendations.append(
                "建议抽样复核差评月份的评论内容，定位是否由物流延迟、商品质量、"
                "错发漏发或售后响应变慢引起。"
            )

    dimension_payload = queries.get("dimension_freight_analysis", {})
    dimension_df = dimension_payload.get("data")

    if dimension_df is not None and not dimension_df.empty:

        high_freight_category = dimension_df.sort_values(
            by="avg_freight_value",
            ascending=False,
        ).iloc[0]

        highlights.append(
            "平均运费最高的品类是 "
            f"{high_freight_category['product_category']}，"
            f"平均运费为 {high_freight_category['avg_freight_value']:.2f}。"
        )

        recommendations.append(
            "建议结合商品重量和体积，复核高运费品类的计费规则、包装方案和承运商策略。"
        )

    # =====================
    # Prophet预测分析
    # =====================
    if forecast is not None:

        highlights.append("系统已生成未来6周销售预测结果。")

        try:

            future_avg = forecast[forecast["is_forecast"] == True]["yhat"].mean()

            if future_avg > 1200000:

                recommendations.append(
                    "预测销售额维持较高水平，建议提前准备库存并扩大营销预算。"
                )

            else:

                recommendations.append(
                    "预测销售增长趋缓，建议控制库存风险并优化运营成本。"
                )

        except Exception:

            recommendations.append(
                "预测结果已生成，建议结合销售趋势制定库存和营销计划。"
            )

    # =====================
    # LLM商业建议
    # =====================
    try:

        llm_context = []

        llm_context.append("=== 业务分析结果 ===")

        for item in highlights:

            llm_context.append(f"- {item}")

        if recommendations:

            llm_context.append("\n=== 规则分析建议 ===")

            for item in recommendations:

                llm_context.append(f"- {item}")

        if review_insights:

            llm_context.append("\n=== NLP评论洞察 ===")

            llm_context.append(review_insights.get("summary", ""))

            keywords = review_insights.get("keywords", [])

            if keywords:

                llm_context.append(f"\n高频关键词：{', '.join(keywords[:10])}")

            if "positive_ratio" in review_insights:

                llm_context.append(f"正向评论占比：{review_insights['positive_ratio']}%")

                llm_context.append(f"中性评论占比：{review_insights['neutral_ratio']}%")

                llm_context.append(f"负向评论占比：{review_insights['negative_ratio']}%")

        if forecast is not None:

            try:

                future_avg = forecast[forecast["is_forecast"] == True]["yhat"].mean()

                future_max = forecast[forecast["is_forecast"] == True]["yhat"].max()

                future_min = forecast[forecast["is_forecast"] == True]["yhat"].min()

                llm_context.append("\n=== 销售预测结果 ===")

                llm_context.append(f"未来平均销售额：{future_avg:,.0f}")

                llm_context.append(f"未来最高销售额：{future_max:,.0f}")

                llm_context.append(f"未来最低销售额：{future_min:,.0f}")

            except Exception:

                pass

        summary_text = "\n".join(llm_context)

        if summary_text.strip():

            llm_advice = generate_business_advice(summary_text)

            print("\n========== AI INPUT ==========")

            print(summary_text)

            print("\n========== AI OUTPUT ==========")

            print(llm_advice)

            print("\n===============================")

    except Exception as e:

        print("[LLM ADVICE ERROR]", e)

    # =====================
    # 默认内容
    # =====================
    if not highlights:

        highlights.append("当前结果暂未匹配到明确的业务异常。")

    if not recommendations:

        recommendations.append(
            "建议进一步细化问题，例如查询销售、配送、支付、品类或卖家表现。"
        )

    # =====================
    # AI建议
    # =====================
    if llm_advice:

        recommendations.append("===== AI运营建议 =====")

        recommendations.append(llm_advice)

    return {"highlights": highlights, "recommendations": recommendations}
