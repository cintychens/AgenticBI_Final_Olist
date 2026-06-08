from agents.llm_agent import generate_business_advice


def generate_advice(state):

    df = state.get("primary", {}).get("data")
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

        highlights.append(f"当前平均准时率为 {avg_rate:.2%}。")

        if avg_rate < 0.80:

            recommendations.append("准时率偏低，建议重点优化物流履约流程。")

        elif avg_rate < 0.90:

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

    # =====================
    # 评论分析
    # =====================
    if review_insights and review_insights.get("summary"):

        highlights.append(review_insights["summary"])

    # =====================
    # Prophet预测分析
    # =====================
    if forecast is not None:

        highlights.append("系统已生成未来6个月销售预测结果。")

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

                llm_context.append(f"Positive: {review_insights['positive_ratio']}%")

                llm_context.append(f"Neutral: {review_insights['neutral_ratio']}%")

                llm_context.append(f"Negative: {review_insights['negative_ratio']}%")

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
