from agents.data_analysis_agent import analyze_question_with_trace
from agents.decision_agent import generate_advice
from agents.review_insight_agent import extract_review_insights
from agents.visualization_agent import create_charts
from agents.what_if_agent import seller_removal_simulation


def run_agent(question, memory=None):

    memory = memory or []

    # =====================
    # 构建上下文
    # =====================

    memory_context = ""

    memory_result = ""

    if memory:

        history = []

        for item in memory[-5:]:

            history.append(
                f"历史问题: {item['question']}"
            )

        memory_context = "\n".join(history)

        latest = memory[-1]

        memory_result = f"""
    最近一次分析：

    问题：
    {latest.get("question","")}

    意图：
    {latest.get("intent","")}

    结果：
    {latest.get("result_preview","")}
    """
    # =====================
    # 带上下文的问题
    # =====================

    question_with_context = question

    if memory_context:

        question_with_context = f"""
    历史对话:

    {memory_context}

    {memory_result}

    当前问题:

    {question}
    """

    # 使用带上下文的问题
    state = analyze_question_with_trace(question_with_context)

    state["memory"] = memory[-5:]
    state["review_insights"] = extract_review_insights(state)
    state["charts"] = create_charts(state["queries"], state.get("forecast"))
    state["advice"] = generate_advice(state)
    state["what_if"] = seller_removal_simulation()

    first_chart = state["charts"][0]["figure"] if state["charts"] else None
    state["data"] = state["primary"]["data"]
    state["chart"] = first_chart

    # 兼容“advice 为列表”的前端要求，同时保留结构化建议。
    state["advice_detail"] = state["advice"]
    state["advice"] = (
        state["advice"]["highlights"] + state["advice_detail"]["recommendations"]
    )

    state["workflow"] = [
        "协调器 Agent：接收自然语言问题并维护会话上下文",
        f"自然语言理解 Agent：识别意图为 {state['intent']['label']}，置信度 {state['intent']['confidence']}",
        "数据分析 Agent：优先查询预聚合视图，无法覆盖时回退基础表",
        "评论洞察 Agent：在评论类问题中提取差评品类与关键词",
        "可视化 Agent：根据字段结构自动选择图表类型",
        "决策智能 Agent：综合指标、预测和评论洞察输出运营建议",
    ]

    return state
