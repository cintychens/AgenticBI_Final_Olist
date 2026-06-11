import pandas as pd
import streamlit as st

from agents.coordinator_agent import run_agent
from utils.performance_test import benchmark_monthly_sales
from datetime import datetime

EXAMPLE_QUESTIONS = [
    "查看月度销售趋势",
    "哪个州的销售额最高？",
    "分析品类销售表现",
    "平台配送准时率怎么样？",
    "哪种支付方式最受欢迎？",
    "哪些卖家评分最低？",
    "预测未来6周销售趋势",
    "分析用户评论情感",
]


def _inject_style():
    st.markdown(
        """
        <style>
        /* 全局样式 */
        .stApp {
            background: #f0f2f6;
        }

        /* 侧边栏样式 */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
            border-right: 1px solid #e4e7eb;
            padding: 1rem 0;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #1e293b;
        }

        /* 头部卡片样式 */
        .main-header {
            background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
            padding: 1.8rem 2rem;
            border-radius: 20px;
            margin-bottom: 1.8rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }

        .main-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
            margin: 0;
            letter-spacing: -0.3px;
        }

        .main-subtitle {
            color: rgba(255, 255, 255, 0.85);
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }

        /* 通用卡片样式 */
        .section-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border: 1px solid #e9ecef;
        }

        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e9ecef;
            display: inline-block;
        }

        /* KPI 卡片样式 */
        .kpi-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 1rem 1.25rem;
            border: 1px solid #e9ecef;
            transition: all 0.2s ease;
        }

        .kpi-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .kpi-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .kpi-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1e3a5f;
            line-height: 1.2;
        }

        /* Agent 标签样式 */
        .agent-pill {
            display: block;
            background: #f1f5f9;
            color: #1e3a5f;
            border-radius: 10px;
            padding: 0.5rem 0.75rem;
            margin: 0.35rem 0;
            font-size: 0.85rem;
            font-weight: 500;
            border-left: 3px solid #3b82f6;
        }

        /* 工作流样式 */
        .workflow-box {
            background: #f8fafc;
            border-radius: 12px;
            padding: 0.8rem 1rem;
            font-size: 0.85rem;
            color: #475569;
            line-height: 1.6;
            border: 1px solid #e2e8f0;
        }

        /* 建议卡片样式 */
        .suggestion-card {
            background: #fefce8;
            border-left: 3px solid #eab308;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin: 0.6rem 0;
            font-size: 0.85rem;
            color: #854d0e;
        }

        /* 按钮样式优化 */
        div.stButton > button {
            border-radius: 10px;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        div.stButton > button: hover {
            transform: translateY(-1px);
        }

        /* 主要按钮 */
        div.stButton > button[kind="primary"] {
            background-color: #1e3a5f;
        }

        /* 侧边栏按钮 */
        [data-testid="stSidebar"] div.stButton > button {
            background: transparent;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            text-align: left;
            justify-content: flex-start;
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
        }

        /* 文本框样式 */
        .stTextArea textarea {
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            font-size: 0.9rem;
        }

        .stTextArea textarea:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
        }

        /* 数据表格样式 */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        /* 指标行间距 */
        .stMetrics {
            gap: 1rem;
        }

        /* 侧边栏分隔线 */
        hr {
            margin: 1rem 0;
            border-color: #e9ecef;
        }

        /* 信息提示框样式 */
        .stAlert {
            border-radius: 12px;
            border-left-width: 4px;
        }

        /* 图表容器 */
        .stPlotlyChart {
            background: #ffffff;
            border-radius: 12px;
            padding: 0.5rem;
        }

        /* 优化滚动条 */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f5f9;
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }

        /* 响应式调整 */
        @media (max-width: 768px) {
            .main-title {
                font-size: 1.3rem;
            }
            .kpi-value {
                font-size: 1.2rem;
            }
            .section-card {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session():
    st.session_state.setdefault("question_input", "")
    st.session_state.setdefault("response", None)
    st.session_state.setdefault("chat_history", [])


def _normalize_response(response):
    """Support both the required simple response shape and richer agent traces."""
    if response is None:
        return pd.DataFrame(), None, []

    data = response.get("data")
    chart = response.get("chart")
    advice = response.get("advice", [])

    if data is None and "primary" in response:
        data = response["primary"].get("data")

    if chart is None and response.get("charts"):
        first_chart = response["charts"][0]
        chart = (
            first_chart.get("figure") if isinstance(first_chart, dict) else first_chart
        )

    if isinstance(advice, dict):
        advice_items = []
        advice_items.extend(advice.get("highlights", []))
        advice_items.extend(advice.get("recommendations", []))
        if not advice_items and advice.get("answer"):
            advice_items = [
                line.strip("- ").strip()
                for line in advice["answer"].splitlines()
                if line.strip()
            ]
        advice = advice_items

    if data is None:
        data = pd.DataFrame()

    return data, chart, advice or []


def _format_number(value, suffix=""):
    if value is None:
        return "-"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M{suffix}"
    if abs(value) >= 1_000:
        return f"{value:,.0f}{suffix}"
    return f"{value:,.2f}{suffix}"


def _collect_kpis(result):
    if result is None or result.empty:
        return []

    kpi_rules = [
        ("total_gmv", "Total GMV", "sum", ""),
        ("total_orders", "Total Orders", "sum", ""),
        ("avg_basket", "Avg Basket", "mean", ""),
        ("on_time_rate", "Avg On-Time Rate", "mean", "%"),
        ("avg_delivery_days", "Avg Delivery Days", "mean", " days"),
        ("total_transactions", "Total Transactions", "sum", ""),
    ]

    kpis = []
    for column, label, agg, suffix in kpi_rules:
        if column not in result.columns:
            continue

        series = pd.to_numeric(result[column], errors="coerce").dropna()
        if series.empty:
            continue

        value = float(series.sum() if agg == "sum" else series.mean())
        if column == "on_time_rate" and value <= 1:
            value *= 100
        kpis.append((label, _format_number(value, suffix)))

    return kpis


def _render_sidebar():
    st.sidebar.markdown("### Agentic BI")
    st.sidebar.markdown("电商运营分析系统")
    st.sidebar.markdown("---")

    st.sidebar.markdown("#### Agents")

    for agent in [
        "Coordinator Agent",
        "Data Analysis Agent",
        "Visualization Agent",
        "Decision Agent",
        "NLP Agent",
        "Forecast Agent",
        "What-if Agent",
    ]:
        st.sidebar.markdown(
            f"<span class='agent-pill'>{agent}</span>", unsafe_allow_html=True
        )

    st.sidebar.markdown("---")

    st.sidebar.markdown("#### 示例问题")

    for question in EXAMPLE_QUESTIONS:
        if st.sidebar.button(
            question, key=f"example_{question}", use_container_width=True
        ):
            st.session_state["selected_question"] = question

    # =====================
    # Conversation Memory
    # =====================

    history = st.session_state.get("chat_history", [])

    st.sidebar.markdown("---")

    st.sidebar.markdown("#### Conversation Memory")

    if not history:
        st.sidebar.info("暂无历史记录")
    else:
        for item in reversed(history[-5:]):
            st.sidebar.markdown(
                f"""
                <div class='workflow-box'>
                <b>{item['intent']}</b><br>
                {item['question']}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.sidebar.metric("Memory Size", len(history))


def _render_header():
    st.markdown(
        """
        <div class="main-header">
            <div class="main-title">Agentic BI E-Commerce Intelligence System</div>
            <div class="main-subtitle">多智能体协作 · 电商运营智能分析与决策支持</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_input_area():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>自然语言查询</div>", unsafe_allow_html=True)

    default_question = st.session_state.get("selected_question", "")

    question = st.text_area(
        "请输入业务问题",
        value=default_question,
        key="question_input",
        height=100,
        placeholder="例如：平台配送准时率怎么样？",
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        analyze = st.button("开始智能分析", type="primary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if analyze:
        if not question.strip():
            st.warning("请输入业务问题后再开始分析。")
        else:
            with st.spinner("Coordinator Agent 正在分析问题..."):
                # =====================
                # 传入历史记忆
                # =====================
                response = run_agent(question, st.session_state["chat_history"])

                st.session_state["response"] = response

            intent = response.get("intent", {}).get("label", "unknown")

            view_name = response.get("primary", {}).get("view", "")

            # =====================
            # 保存记忆
            # =====================
            preview = []

            try:
                preview = (
                    response.get("primary", {}).get("data").head(3).to_dict("records")
                )
            except Exception:
                preview = []

            st.session_state["chat_history"].append(
                {
                    "question": question,
                    "intent": intent,
                    "view": view_name,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "result_preview": preview,
                }
            )

            # 最多保留最近10轮
            st.session_state["chat_history"] = st.session_state["chat_history"][-10:]


def _render_kpis(result):
    st.markdown("<div class='section-title'>关键指标概览</div>", unsafe_allow_html=True)
    kpis = _collect_kpis(result)

    if not kpis:
        st.info("当前结果中暂无可展示的 KPI 字段。")
        return

    cols = st.columns(min(4, len(kpis)))
    for index, (label, value) in enumerate(kpis):
        with cols[index % len(cols)]:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_charts(charts):
    st.markdown("<div class='section-title'>可视化图表</div>", unsafe_allow_html=True)

    if not charts:
        st.info("当前结果暂未匹配到合适的图表类型。")
        return

    TITLE_MAPPING = {
        "forecast": "Sales Forecast Analysis",
        "positive_wordcloud": "Positive Reviews WordCloud",
        "negative_wordcloud": "Negative Reviews WordCloud",
        "payment_installment_heatmap": "Payment × Installment Heatmap",
        "weight_freight_scatter": "Weight vs Freight Cost Analysis",
        "state_geo_map": "Brazil Sales Distribution Map",
        "main_query": "Business Analysis",
    }

    for chart_item in charts:
        chart_name = chart_item.get("name", "chart")
        figure = chart_item.get("figure")
        title = TITLE_MAPPING.get(chart_name, chart_name.replace("_", " ").title())

        st.markdown(f"### {title}")
        st.plotly_chart(figure, width="stretch")


def _render_table(result):
    st.markdown("<div class='section-title'>数据详情</div>", unsafe_allow_html=True)
    if result is None or result.empty:
        st.warning("未查询到数据")
        return
    st.dataframe(result, use_container_width=True)


def _render_advice(advice):
    st.markdown("<div class='section-title'>决策建议</div>", unsafe_allow_html=True)
    if not advice:
        st.info("暂无决策建议")
        return

    for item in advice:
        st.markdown(
            f"<div class='suggestion-card'>{item}</div>", unsafe_allow_html=True
        )


def _render_nlp_insights(review_insights):
    if not review_insights:
        return

    st.markdown("<div class='section-title'>NLP评论洞察</div>", unsafe_allow_html=True)
    st.markdown(review_insights.get("summary", ""))


def _render_what_if(what_if):
    if not what_if:
        return

    st.markdown(
        "<div class='section-title'>What-if Analysis</div>", unsafe_allow_html=True
    )

    st.markdown(f"""
    当前平台平均评分：

    **{what_if['current_score']}**

    如果移除 Top 20 高差评卖家：

    **{what_if['removed_sellers']} 个卖家**
    （本次 Top 20 最高评分阈值 ≤ {what_if['threshold']}）

    优化后评分：

    **{what_if['improved_score']}**

    预计提升：

    **+{what_if['improvement']}**
    """)


def _render_performance_benchmark():
    st.markdown(
        "<div class='section-title'>Pre-Aggregated Query Performance Benchmark</div>",
        unsafe_allow_html=True,
    )

    if st.button("运行性能对比测试", use_container_width=True):
        with st.spinner("正在对比原始表 JOIN 查询与预聚合视图查询..."):
            result = benchmark_monthly_sales()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Raw JOIN Query", f"{result['raw_time']:.4f}s")

        with col2:
            st.metric("Pre-Aggregated Query", f"{result['view_time']:.4f}s")

        with col3:
            st.metric("Speedup", f"{result['speedup']:.2f}x")

        st.markdown("#### 查询结果规模")

        col4, col5 = st.columns(2)

        with col4:
            st.metric("Raw Query Rows", result["raw_rows"])

        with col5:
            st.metric("View Query Rows", result["view_rows"])

        with st.expander("查看原始表 JOIN SQL"):
            st.code(result["raw_sql"], language="sql")

        with st.expander("查看预聚合视图 SQL"):
            st.code(result["view_sql"], language="sql")


def run_dashboard():
    st.set_page_config(
        page_title="Agentic BI Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_session()
    _inject_style()

    _render_header()

    # 先处理用户输入
    _render_input_area()

    # 再渲染侧边栏
    _render_sidebar()

    response = st.session_state.get("response")

    result, chart, advice = _normalize_response(response)

    charts = []

    if response:
        charts = response.get("charts", [])

    col_left, col_right = st.columns([2, 1])

    with col_left:
        with st.container():
            _render_kpis(result)

        with st.container():
            _render_charts(charts)

    with col_right:
        with st.container():
            _render_performance_benchmark()

            if response:
                _render_nlp_insights(response.get("review_insights", {}))

            if response:
                _render_what_if(response.get("what_if"))


if __name__ == "__main__":
    run_dashboard()
