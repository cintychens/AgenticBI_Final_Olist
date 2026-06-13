from openai import OpenAI

from config.settings import VECTOR_API_KEY, VECTOR_BASE_URL, MODEL_NAME

client = OpenAI(api_key=VECTOR_API_KEY, base_url=VECTOR_BASE_URL)


def _rule_based_intent(question: str):
    text = str(question).lower()

    if any(word in text for word in ["预测", "未来", "forecast", "6周", "6 周"]):
        return "forecast"

    if any(word in text for word in ["评论", "评价", "差评品类", "差评原因", "情感", "词云", "review"]):
        return "review"

    if any(word in text for word in ["支付", "分期", "payment", "installment", "信用卡"]):
        return "payment"

    if any(word in text for word in ["准时", "交付", "配送", "延迟", "物流", "运费", "重量", "尺寸", "delivery", "freight"]):
        return "delivery"

    if any(word in text for word in ["卖家", "seller", "差评率"]):
        return "seller"

    if any(word in text for word in ["州", "地区", "东北部", "区域", "state"]):
        return "state"

    if any(word in text for word in ["品类", "产品", "category"]):
        return "category"

    if any(word in text for word in ["gmv", "销售", "销售额", "月度", "趋势", "订单"]):
        return "sales"

    return None

INTENT_PROMPT = """
你是Agentic BI系统中的意图识别Agent。

请判断用户问题属于以下哪一个类别。

只允许返回下面八个单词之一：

sales
state
category
delivery
payment
seller
forecast
review

分类说明：

sales：
销售趋势、GMV、营业额、订单趋势

state：
州销售额、地区销售额、区域市场

category：
商品品类、产品分类、品类表现

delivery：
配送时效、物流、准时率、延迟

payment：
支付方式、分期付款、信用卡

seller：
卖家绩效、评分、差评卖家

forecast：
未来销售预测、预测未来6周销售额、销售额预测、趋势预测

review：

评论分析
用户评价
评论关键词
好评与差评分析
词云分析
评论主题

如果用户的问题包含：

第二名
第三名
第一名
那个州
这个州
它
他们
继续分析
继续
刚才那个
上一个结果

请结合历史上下文理解真实意图。

例如：

哪个州销售额最高
→ state

第二名呢
→ state

那个州配送情况怎么样
→ delivery

继续分析评论
→ review

不要解释。
不要输出其它内容。
只返回类别名称。
"""


def classify_question(question: str) -> str:
    """
    使用大模型识别业务意图
    """

    rule_intent = _rule_based_intent(question)

    if rule_intent:
        return rule_intent

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
        )

        result = response.choices[0].message.content.strip().lower()

        allowed = {
            "sales",
            "state",
            "category",
            "delivery",
            "payment",
            "seller",
            "forecast",
            "review",
        }

        if result in allowed:
            return result

        return "sales"

    except Exception as e:

        print("[LLM ERROR]", e)

        return "sales"


def generate_business_advice(summary):

    try:

        prompt = f"""
你是一名资深电商运营与商业智能（Business Intelligence）顾问。

请根据以下业务分析结果进行综合推理：

{summary}

重要约束：
1. 数据库查询返回的原始取值必须保持原样，不要翻译、改写或本地化。
2. 例如 credit_card、boleto、SP、seller_id、product_category、评论关键词和评论原文等具体取值，必须按数据里的原始写法输出。
3. 面向业务用户解释字段或指标时，请使用中文名称，例如 total_gmv 写成“总GMV”，total_orders 写成“订单量”，avg_review_score 写成“平均评分”。
4. 只有你自己生成的解释、结论、原因归纳和运营建议必须使用中文。

请输出以下内容：

【一、核心发现】
总结当前业务表现中的关键现象。

【二、风险分析】
指出可能存在的运营风险或异常。

【三、销售趋势判断】
结合已有指标与预测结果，判断未来销售走势。

【四、运营优化建议】
给出3~5条具体、可执行的运营建议。

【五、优先级最高的行动】
列出最值得立即执行的三项措施。

要求：

1. 使用中文回答
2. 分点输出
3. 不少于200字
4. 建议必须具有可执行性
5. 结合销售、物流、支付、评论、卖家绩效等维度综合分析
"""

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """
你是一名拥有10年以上经验的电商运营顾问。

你擅长：

- GMV增长分析
- 用户行为分析
- 商品运营分析
- 卖家绩效管理
- 物流履约优化
- 商业决策支持

你的任务是根据业务数据给出专业、具体、可执行的运营建议。
不要泛泛而谈。
""",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1200,
        )

        return response.choices[0].message.content

    except Exception as e:

        print("[LLM ADVICE ERROR]", e)

        return "暂时无法生成AI建议。"
