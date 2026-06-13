import html

import pandas as pd
import streamlit as st

from agents.coordinator_agent import run_agent
from agents.memory_agent import remember_turn
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

        .chat-panel {
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 16px;
            padding: 1rem;
            margin: 1rem 0;
            min-height: 520px;
            max-height: 72vh;
            overflow-y: auto;
        }

        .chat-turn {
            margin: 0.75rem 0;
            display: flex;
            flex-direction: column;
        }

        .chat-user,
        .chat-agent {
            max-width: 86%;
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            font-size: 0.9rem;
            line-height: 1.55;
            word-break: break-word;
        }

        .chat-user {
            align-self: flex-end;
            margin-left: auto;
            background: #1e3a5f;
            color: #ffffff;
            border-bottom-right-radius: 4px;
        }

        .chat-agent {
            align-self: flex-start;
            margin-right: auto;
            background: #f8fafc;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 4px;
        }

        .chat-meta {
            font-size: 0.72rem;
            color: #64748b;
            margin-bottom: 0.35rem;
            font-weight: 600;
        }

        .chat-preview {
            margin-top: 0.5rem;
            font-size: 0.78rem;
            color: #475569;
        }

        .chat-empty {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.6;
            padding: 1rem;
            background: #f8fafc;
            border: 1px dashed #cbd5e1;
            border-radius: 12px;
        }

        .bubble-row {
            display: flex;
            width: 100%;
            margin: 0.6rem 0;
        }

        .bubble-row.user-row {
            justify-content: flex-end;
        }

        .bubble-row.agent-row {
            justify-content: flex-start;
        }

        .bubble {
            max-width: 86%;
            border-radius: 14px;
            padding: 0.7rem 0.85rem;
            font-size: 0.9rem;
            line-height: 1.55;
            word-break: break-word;
        }

        .user-bubble {
            background: #1e3a5f;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .agent-bubble {
            background: white;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 4px;
        }

        .quick-question-title {
            color: #475569;
            font-size: 0.78rem;
            font-weight: 700;
            margin: 0.6rem 0 0.35rem;
        }

        [data-testid="stVerticalBlock"] [data-testid="stChatMessage"] {
            margin-bottom: 0.65rem;
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

        /* Modern BI visual refinement overrides */
        .stApp {
            background: #F8FAFC;
            color: #111827;
            font-family: Inter, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #1E3A8A 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.10);
            box-shadow: 12px 0 36px rgba(15, 23, 42, 0.14);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #E5E7EB;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4 {
            color: #FFFFFF;
            font-weight: 800;
            letter-spacing: 0;
        }

        [data-testid="stSidebar"] hr {
            border-color: rgba(255, 255, 255, 0.16);
        }

        .main-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            box-shadow: 0 18px 42px rgba(30, 58, 138, 0.24);
        }

        .main-title {
            color: #FFFFFF;
            font-weight: 800;
            letter-spacing: 0;
        }

        .main-subtitle {
            color: #DBEAFE;
            font-size: 0.95rem;
        }

        .section-card,
        .chat-panel,
        .workflow-box,
        .suggestion-card,
        .forecast-summary,
        .stPlotlyChart {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
        }

        .section-card,
        .chat-panel,
        .workflow-box,
        .suggestion-card,
        .forecast-summary {
            padding: 1rem;
        }

        .section-title {
            color: #111827;
            font-size: 1rem;
            font-weight: 800;
            margin: 1.15rem 0 0.85rem;
        }

        .section-title::after {
            background: #E5E7EB;
            height: 1px;
        }

        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.07);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .kpi-card:hover {
            transform: translateY(-3px);
            border-color: #BFDBFE;
            box-shadow: 0 18px 38px rgba(30, 58, 138, 0.12);
        }

        .kpi-label {
            color: #6B7280;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .kpi-value {
            color: #1E3A8A;
            font-size: 1.65rem;
            font-weight: 850;
            letter-spacing: 0;
        }

        .agent-pill {
            background: rgba(255, 255, 255, 0.10);
            color: #EAF2FF;
            border-left: 4px solid #60A5FA;
            border-radius: 12px;
            font-weight: 750;
            transition: transform 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
        }

        .agent-pill:hover {
            background: rgba(59, 130, 246, 0.26);
            transform: translateX(2px);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
        }

        div.stButton > button {
            border-radius: 12px;
            border: 1px solid #E5E7EB;
            background: #FFFFFF;
            color: #1E3A8A;
            font-weight: 750;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease;
        }

        div.stButton > button:hover {
            background: linear-gradient(135deg, #EFF6FF 0%, #FFFFFF 100%);
            border-color: #93C5FD;
            color: #1D4ED8;
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(30, 58, 138, 0.12);
        }

        div.stButton > button:active {
            transform: scale(0.98);
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: #FFFFFF;
            border-color: #1E40AF;
            box-shadow: 0 10px 24px rgba(30, 58, 138, 0.22);
        }

        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
            color: #FFFFFF;
            border-color: #60A5FA;
        }

        .stTextArea textarea {
            background: #F9FAFB;
            border: 1px solid #D1D5DB;
            border-radius: 14px;
            color: #111827;
            font-size: 0.95rem;
            padding: 0.85rem 0.95rem;
            box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
            transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
        }

        .stTextArea textarea:focus {
            background: #FFFFFF;
            border-color: #3B82F6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
        }

        .stPlotlyChart {
            padding: 0.9rem;
            margin: 0.9rem 0 1.6rem;
            overflow: hidden;
        }

        .chat-panel {
            padding: 1rem;
        }

        .bubble {
            border-radius: 16px;
            padding: 0.78rem 0.95rem;
            font-size: 0.95rem;
            line-height: 1.65;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
        }

        .user-bubble {
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.16);
        }

        .agent-bubble {
            background: #FFFFFF;
            color: #1E293B;
            border: 1px solid #E5E7EB;
        }

        .chat-meta {
            color: rgba(255, 255, 255, 0.72);
            font-size: 0.72rem;
            font-weight: 750;
        }

        .agent-bubble .chat-meta {
            color: #64748B;
        }

        .chat-preview {
            color: #64748B;
            font-size: 0.82rem;
            margin-top: 0.45rem;
        }

        .memory-card {
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 14px;
            color: #E5E7EB;
        }

        .memory-card strong {
            color: #FFFFFF;
        }

        .sidebar-brand {
            padding: 0.4rem 0 0.9rem;
        }

        .sidebar-brand-title {
            color: #FFFFFF;
            font-size: 1.15rem;
            font-weight: 850;
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }

        .sidebar-brand-subtitle {
            color: #CBD5E1;
            font-size: 0.78rem;
            line-height: 1.5;
        }

        .sidebar-section-label {
            color: #93A4BC;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin: 1rem 0 0.55rem;
        }

        .history-list {
            display: flex;
            flex-direction: column;
            gap: 0.45rem;
        }

        .history-card {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            color: #E5E7EB;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
        }

        .history-card.active {
            background: rgba(59, 130, 246, 0.28);
            border-color: rgba(147, 197, 253, 0.55);
        }

        .history-question {
            color: #FFFFFF;
            font-size: 0.86rem;
            font-weight: 700;
            line-height: 1.45;
            margin-bottom: 0.35rem;
        }

        .history-meta {
            color: #CBD5E1;
            font-size: 0.72rem;
            line-height: 1.35;
        }

        .history-empty {
            color: #CBD5E1;
            background: rgba(255, 255, 255, 0.07);
            border: 1px dashed rgba(203, 213, 225, 0.34);
            border-radius: 14px;
            padding: 0.8rem;
            font-size: 0.82rem;
            line-height: 1.5;
        }

        [data-testid="stSidebar"] div.stButton > button {
            background: rgba(255, 255, 255, 0.10);
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 14px;
            justify-content: center;
            text-align: center;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.16);
        }

        [data-testid="stSidebar"] div.stButton > button:hover {
            background: rgba(59, 130, 246, 0.35);
            color: #FFFFFF;
            border-color: rgba(147, 197, 253, 0.62);
        }

        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 0.85rem 1rem;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        }

        ::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #3B82F6;
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
    history = st.session_state.get("chat_history", [])

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">Agentic BI</div>
            <div class="sidebar-brand-subtitle">电商运营分析系统</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.button("＋ 新分析", use_container_width=True)

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "<div class='sidebar-section-label'>Conversation History</div>",
        unsafe_allow_html=True,
    )

    if not history:
        st.sidebar.markdown(
            """
            <div class="history-empty">
                暂无历史问题。开始一次分析后，这里会显示最近的对话记录。
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        latest_question = str(history[-1].get("question", "")) if history else ""
        history_cards = []

        for item in reversed(history[-10:]):
            question = html.escape(str(item.get("question", "")))
            intent = html.escape(str(item.get("intent", "analysis")))
            timestamp = html.escape(str(item.get("timestamp", "")))
            active_class = (
                " history-card active"
                if str(item.get("question", "")) == latest_question
                else " history-card"
            )

            history_cards.append(
                f'<div class="{active_class.strip()}">'
                f'<div class="history-question">{question}</div>'
                f'<div class="history-meta">{intent} · {timestamp}</div>'
                "</div>"
            )

        st.sidebar.markdown(
            "<div class='history-list'>" + "".join(history_cards) + "</div>",
            unsafe_allow_html=True,
        )


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
                    "advice_preview": response.get("advice", [])[:3],
                }
            )

            # 最多保留最近10轮
            st.session_state["chat_history"] = st.session_state["chat_history"][-10:]


def _render_conversation_area():
    history = st.session_state.get("chat_history", [])

    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    if not history:
        st.info("当前会话还没有问题。你可以先输入一个业务问题，然后继续追问上一轮结果。")
        return

    for item in history[-6:]:
        question = html.escape(str(item.get("question", "")))
        intent = html.escape(str(item.get("intent", "unknown")))
        view_name = html.escape(str(item.get("view", "")))
        timestamp = html.escape(str(item.get("timestamp", "")))
        preview = html.escape(str(item.get("result_preview", "")))
        advice_preview = item.get("advice_preview", [])

        if isinstance(advice_preview, list) and advice_preview:
            advice_text = html.escape(" | ".join(str(text) for text in advice_preview[:2]))
        else:
            advice_text = "Analysis completed. See charts and recommendations on the right."

        st.markdown(
            f"""
            <div class="chat-turn">
                <div class="chat-user">
                    <div class="chat-meta" style="color: rgba(255,255,255,0.75);">You · {timestamp}</div>
                    {question}
                </div>
            </div>
            <div class="chat-turn">
                <div class="chat-agent">
                    <div class="chat-meta">Agent · intent: {intent} · view: {view_name}</div>
                    {advice_text}
                    <div class="chat-preview">Result preview: {preview}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )



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
        "dimension_freight_analysis": "Product Size vs Freight Cost Analysis",
        "top_negative_categories": "Top 10 Negative Review Categories",
        "sales_anomaly_detection": "Monthly GMV Anomaly Detection",
        "state_order_drop_anomaly": "State Order Drop Anomaly Detection",
        "review_rate_spike_anomaly": "Negative Review Rate Spike Detection",
        "state_geo_map": "Brazil Sales Distribution Map",
        "state_avg_basket": "Average Basket by State",
        "main_query": "Business Analysis",
        "sales_query": "Monthly Sales Trend",
        "state_query": "State Sales Ranking",
        "delivery_query": "Delivery Performance",
        "payment_query": "Payment Analysis",
        "category_query": "Category Sales Analysis",
        "seller_query": "Low-Rated Seller Analysis",
        "review_query": "Review Insight Data",
        "northeast_return_risk": "Northeast Return / Cancellation Risk",
    }

    INTENT_TITLE_MAPPING = {
        "sales": "Monthly Sales Trend",
        "state": "State Sales Ranking",
        "category": "Category Sales Analysis",
        "delivery": "Delivery Performance",
        "payment": "Payment Analysis",
        "seller": "Low-Rated Seller Analysis",
        "review": "Review Insight Data",
        "forecast": "Sales Forecast Analysis",
    }

    CHART_PRIORITY = {
        "forecast": 0,
        "main_query": 10,
        "sales_query": 20,
        "state_query": 30,
        "state_avg_basket": 35,
        "delivery_query": 40,
        "payment_query": 50,
        "payment_installment_heatmap": 55,
        "category_query": 60,
        "seller_query": 70,
        "top_negative_categories": 80,
        "positive_wordcloud": 90,
        "negative_wordcloud": 91,
        "weight_freight_scatter": 100,
        "dimension_freight_analysis": 101,
        "state_geo_map": 110,
        "sales_anomaly_detection": 120,
        "state_order_drop_anomaly": 121,
        "review_rate_spike_anomaly": 122,
    }

    def _chart_priority(item):
        chart_name = item.get("name", "chart")
        chart_intent = item.get("intent")

        if chart_name == "main_query":
            return {
                "forecast": 0,
                "sales": 20,
                "state": 30,
                "delivery": 40,
                "payment": 50,
                "category": 60,
                "seller": 70,
                "review": 80,
            }.get(chart_intent, 10)

        return CHART_PRIORITY.get(chart_name, 999)

    sorted_charts = sorted(charts, key=_chart_priority)

    for chart_index, chart_item in enumerate(sorted_charts):
        chart_name = chart_item.get("name", "chart")
        figure = chart_item.get("figure")
        chart_intent = chart_item.get("intent")

        if chart_name == "main_query" and chart_intent in INTENT_TITLE_MAPPING:
            title = INTENT_TITLE_MAPPING[chart_intent]
        else:
            title = TITLE_MAPPING.get(chart_name, chart_name.replace("_", " ").title())

        st.markdown(f"### {title}")
        st.plotly_chart(
            figure,
            width="stretch",
            key=f"chart_{chart_index}_{chart_name}",
        )


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

        if result.get("cases"):
            benchmark_df = pd.DataFrame(
                [
                    {
                        "Analysis Question": case["question"],
                        "Raw JOIN Query": f"{case['raw_time']:.4f}s",
                        "Pre-Aggregated Query": f"{case['view_time']:.4f}s",
                        "Speedup": f"{case['speedup']:.2f}x",
                        "Raw Rows": case["raw_rows"],
                        "Pre-Aggregated Rows": case["view_rows"],
                    }
                    for case in result["cases"]
                ]
            )
            st.dataframe(benchmark_df, use_container_width=True, hide_index=True)
            st.metric("Average Speedup", f"{result['average_speedup']:.2f}x")

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


def _render_conversation_area():
    history = st.session_state.get("chat_history", [])
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    if not history:
        st.markdown(
            """
            <div class="chat-panel">
                <div class="chat-empty">
                    当前会话还没有问题。先输入一个业务问题，之后可以像聊天一样继续追问上一轮结果。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    turns = []

    for item in history[-8:]:
        question = html.escape(str(item.get("question", "")))
        intent = html.escape(str(item.get("intent", "unknown")))
        view_name = html.escape(str(item.get("view", "")))
        timestamp = html.escape(str(item.get("timestamp", "")))
        preview = html.escape(str(item.get("result_preview", "")))
        advice_preview = item.get("advice_preview", [])

        if isinstance(advice_preview, list) and advice_preview:
            advice_text = html.escape(" | ".join(str(text) for text in advice_preview[:2]))
        else:
            advice_text = "Analysis completed. See charts and recommendations on the right."

        turns.append(
            (
                '<div class="chat-turn">'
                '<div class="chat-user">'
                f'<div class="chat-meta" style="color: rgba(255,255,255,0.75);">You · {timestamp}</div>'
                f"{question}"
                "</div>"
                "</div>"
                '<div class="chat-turn">'
                '<div class="chat-agent">'
                f'<div class="chat-meta">Agent · intent: {intent} · view: {view_name}</div>'
                f"{advice_text}"
                f'<div class="chat-preview">Result preview: {preview}</div>'
                "</div>"
                "</div>"
            )
        )

    st.markdown(
        f"<div class='chat-panel'>{''.join(turns)}</div>",
        unsafe_allow_html=True,
    )


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    if history:
        turns = []

        for item in history[-8:]:
            question = html.escape(str(item.get("question", "")))
            intent = html.escape(str(item.get("intent", "unknown")))
            view_name = html.escape(str(item.get("view", "")))
            timestamp = html.escape(str(item.get("timestamp", "")))
            preview = html.escape(str(item.get("result_preview", "")))
            advice_preview = item.get("advice_preview", [])

            if isinstance(advice_preview, list) and advice_preview:
                advice_text = html.escape(
                    " | ".join(str(text) for text in advice_preview[:2])
                )
            else:
                advice_text = (
                    "Analysis completed. See charts and recommendations on the right."
                )

            turns.append(
                f"""
                <div class="chat-turn">
                    <div class="chat-user">
                        <div class="chat-meta" style="color: rgba(255,255,255,0.75);">You · {timestamp}</div>
                        {question}
                    </div>
                </div>
                <div class="chat-turn">
                    <div class="chat-agent">
                        <div class="chat-meta">Agent · intent: {intent} · view: {view_name}</div>
                        {advice_text}
                        <div class="chat-preview">Result preview: {preview}</div>
                    </div>
                </div>
                """
            )

        st.markdown(
            f"<div class='chat-panel'>{''.join(turns)}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="chat-panel">
                <div class="chat-empty">
                    当前会话还没有问题。先输入一个业务问题，之后可以像聊天一样继续追问上一轮结果。
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    analyze = st.button("发送并分析", type="primary", use_container_width=True)

    if analyze:
        if not question.strip():
            st.warning("请输入业务问题后再发送。")
            return

        with st.spinner("Coordinator Agent 正在分析问题..."):
            response = run_agent(question, st.session_state["chat_history"])
            st.session_state["response"] = response
            st.session_state["chat_history"] = remember_turn(
                st.session_state["chat_history"],
                question,
                response,
            )


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

    _render_conversation_area()

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
    _render_sidebar()

    chat_col, result_col = st.columns([1.05, 2.95], gap="large")

    with chat_col:
        _render_chat_panel()

    response = st.session_state.get("response")
    result, chart, advice = _normalize_response(response)
    charts = response.get("charts", []) if response else []

    with result_col:
        _render_kpis(result)
        _render_charts(charts)


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    if history:
        for item in history[-8:]:
            with st.chat_message("user"):
                st.write(item.get("question", ""))

            advice_preview = item.get("advice_preview", [])
            if isinstance(advice_preview, list) and advice_preview:
                answer = "\n\n".join(str(text) for text in advice_preview[:2])
            else:
                answer = "分析已完成，右侧展示了对应的指标、图表和决策建议。"

            with st.chat_message("assistant"):
                st.write(answer)
    else:
        st.info("当前会话还没有问题。先输入一个业务问题，之后可以像聊天一样继续追问上一轮结果。")

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    analyze = st.button("发送并分析", type="primary", use_container_width=True)

    if analyze:
        if not question.strip():
            st.warning("请输入业务问题后再发送。")
            return

        with st.spinner("Coordinator Agent 正在分析问题..."):
            response = run_agent(question, st.session_state["chat_history"])
            st.session_state["response"] = response
            st.session_state["chat_history"] = remember_turn(
                st.session_state["chat_history"],
                question,
                response,
            )


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    with st.container(height=620):
        if history:
            for item in history[-8:]:
                with st.chat_message("user"):
                    st.write(item.get("question", ""))

                advice_preview = item.get("advice_preview", [])
                if isinstance(advice_preview, list) and advice_preview:
                    answer = "\n\n".join(str(text) for text in advice_preview[:2])
                else:
                    answer = "分析已完成，右侧展示了对应的指标、图表和决策建议。"

                with st.chat_message("assistant"):
                    st.write(answer)
        else:
            st.info("当前会话还没有问题。先选择一个快捷问题，或在下方输入业务问题。")

        st.markdown(
            "<div class='quick-question-title'>快捷问题</div>",
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(EXAMPLE_QUESTIONS), 2):
            cols = st.columns(2)
            for offset, question_item in enumerate(
                EXAMPLE_QUESTIONS[row_start: row_start + 2]
            ):
                with cols[offset]:
                    if st.button(
                        question_item,
                        key=f"chat_example_{row_start}_{offset}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_question"] = question_item
                        st.session_state["chat_question_input"] = question_item
                        st.rerun()

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    analyze = st.button("发送并分析", type="primary", use_container_width=True)

    if analyze:
        if not question.strip():
            st.warning("请输入业务问题后再发送。")
            return

        with st.spinner("Coordinator Agent 正在分析问题..."):
            response = run_agent(question, st.session_state["chat_history"])
            st.session_state["response"] = response
            st.session_state["chat_history"] = remember_turn(
                st.session_state["chat_history"],
                question,
                response,
            )


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    with st.container(height=620):
        if history:
            bubble_html = []

            for item in history[-8:]:
                user_text = html.escape(str(item.get("question", ""))).replace("\n", "<br>")
                advice_preview = item.get("advice_preview", [])

                if isinstance(advice_preview, list) and advice_preview:
                    agent_text = "<br><br>".join(
                        html.escape(str(text)) for text in advice_preview[:2]
                    )
                else:
                    agent_text = "分析已完成，右侧展示了对应的指标、图表和决策建议。"

                bubble_html.append(
                    '<div class="bubble-row user-row">'
                    f'<div class="bubble user-bubble">{user_text}</div>'
                    '</div>'
                    '<div class="bubble-row agent-row">'
                    f'<div class="bubble agent-bubble">{agent_text}</div>'
                    '</div>'
                )

            st.markdown("".join(bubble_html), unsafe_allow_html=True)
        else:
            st.info("当前会话还没有问题。先选择一个快捷问题，或在下方输入业务问题。")

        st.markdown(
            "<div class='quick-question-title'>快捷问题</div>",
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(EXAMPLE_QUESTIONS), 2):
            cols = st.columns(2)
            for offset, question_item in enumerate(
                EXAMPLE_QUESTIONS[row_start: row_start + 2]
            ):
                with cols[offset]:
                    if st.button(
                        question_item,
                        key=f"chat_example_{row_start}_{offset}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_question"] = question_item
                        st.session_state["chat_question_input"] = question_item
                        st.rerun()

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    analyze = st.button("发送并分析", type="primary", use_container_width=True)

    if analyze:
        if not question.strip():
            st.warning("请输入业务问题后再发送。")
            return

        with st.spinner("Coordinator Agent 正在分析问题..."):
            response = run_agent(question, st.session_state["chat_history"])
            st.session_state["response"] = response
            st.session_state["chat_history"] = remember_turn(
                st.session_state["chat_history"],
                question,
                response,
            )


def _submit_chat_question(question):
    question = str(question or "").strip()

    if not question:
        st.warning("请输入业务问题后再发送。")
        return

    with st.spinner("Coordinator Agent 正在分析问题..."):
        response = run_agent(question, st.session_state["chat_history"])
        st.session_state["response"] = response
        st.session_state["chat_history"] = remember_turn(
            st.session_state["chat_history"],
            question,
            response,
        )
        st.session_state["selected_question"] = ""

    st.rerun()


def _append_chat_tool_result(question, answer):
    history = st.session_state.get("chat_history", [])
    history.append(
        {
            "question": question,
            "intent": "tool",
            "view": "",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "result_preview": [],
            "advice_preview": [answer],
        }
    )
    st.session_state["chat_history"] = history[-10:]


def _submit_performance_benchmark_chat():
    with st.spinner("正在运行预聚合视图性能对比测试..."):
        result = benchmark_monthly_sales()

    if result.get("cases"):
        lines = [
            "预聚合查询性能对比 Benchmark",
            "",
            "说明：以下对比展示同一分析问题在使用预聚合前后的查询耗时差异，用于证明预计算优化效果。",
            "",
            (
                f"平均加速倍数：{result['average_speedup']:.2f}x；"
                f"最高加速案例：{result['best_case']}。"
            ),
            "",
        ]

        for case in result["cases"]:
            lines.extend(
                [
                    f"【{case['name']}】",
                    f"- 分析问题：{case['question']}",
                    f"- 原始 JOIN 查询：{case['raw_time']:.4f}s，{case['raw_rows']} 行",
                    f"- 预聚合查询：{case['view_time']:.4f}s，{case['view_rows']} 行",
                    f"- 加速倍数：{case['speedup']:.2f}x",
                    "",
                ]
            )

        answer = "\n".join(lines)
    else:
        answer = (
            "Pre-Aggregated Query Performance Benchmark\n\n"
            f"- Raw JOIN Query: {result['raw_time']:.4f}s\n"
            f"- Pre-Aggregated Query: {result['view_time']:.4f}s\n"
            f"- Speedup: {result['speedup']:.2f}x\n"
            f"- Raw Query Rows: {result['raw_rows']}\n"
            f"- View Query Rows: {result['view_rows']}"
        )

    _append_chat_tool_result("运行性能对比测试", answer)
    st.rerun()


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    with st.container(height=620):
        if history:
            bubble_html = []

            for item in history[-10:]:
                user_text = html.escape(str(item.get("question", ""))).replace("\n", "<br>")
                advice_preview = item.get("advice_preview", [])

                if isinstance(advice_preview, list) and advice_preview:
                    agent_text = "<br><br>".join(
                        html.escape(str(text)) for text in advice_preview[:2]
                    )
                else:
                    agent_text = "分析已完成，右侧展示了对应的指标、图表和决策建议。"

                bubble_html.append(
                    '<div class="bubble-row user-row">'
                    f'<div class="bubble user-bubble">{user_text}</div>'
                    '</div>'
                    '<div class="bubble-row agent-row">'
                    f'<div class="bubble agent-bubble">{agent_text}</div>'
                    '</div>'
                )

            st.markdown("".join(bubble_html), unsafe_allow_html=True)
        else:
            st.info("当前会话还没有问题。先选择一个快捷问题，或在下方输入业务问题。")

        st.markdown(
            "<div class='quick-question-title'>快捷问题</div>",
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(EXAMPLE_QUESTIONS), 2):
            cols = st.columns(2)
            for offset, question_item in enumerate(
                EXAMPLE_QUESTIONS[row_start: row_start + 2]
            ):
                with cols[offset]:
                    if st.button(
                        question_item,
                        key=f"chat_example_submit_{row_start}_{offset}",
                        use_container_width=True,
                    ):
                        _submit_chat_question(question_item)

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    if st.button("发送并分析", type="primary", use_container_width=True):
        _submit_chat_question(question)


def _render_chat_panel():
    st.markdown("<div class='section-title'>Conversation</div>", unsafe_allow_html=True)

    history = st.session_state.get("chat_history", [])

    with st.container(height=720):
        if history:
            bubble_html = []

            for item in history[-10:]:
                user_text = html.escape(str(item.get("question", ""))).replace("\n", "<br>")
                advice_preview = item.get("advice_preview", [])

                if isinstance(advice_preview, list) and advice_preview:
                    agent_text = "<br><br>".join(
                        html.escape(str(text)) for text in advice_preview[:2]
                    )
                else:
                    agent_text = "分析已完成，右侧展示了对应的指标、图表和决策建议。"

                bubble_html.append(
                    '<div class="bubble-row user-row">'
                    f'<div class="bubble user-bubble">{user_text}</div>'
                    '</div>'
                    '<div class="bubble-row agent-row">'
                    f'<div class="bubble agent-bubble">{agent_text}</div>'
                    '</div>'
                )

            st.markdown("".join(bubble_html), unsafe_allow_html=True)
        else:
            st.info("当前会话还没有问题。先选择一个快捷问题，或在下方输入业务问题。")

        st.markdown(
            "<div class='quick-question-title'>快捷工具</div>",
            unsafe_allow_html=True,
        )

        tool_cols = st.columns(2)
        with tool_cols[0]:
            if st.button(
                "运行性能对比测试",
                key="chat_tool_performance",
                use_container_width=True,
            ):
                _submit_performance_benchmark_chat()

        with tool_cols[1]:
            if st.button(
                "NLP评论洞察",
                key="chat_tool_nlp",
                use_container_width=True,
            ):
                _submit_chat_question("分析用户评论情感")

        st.markdown(
            "<div class='quick-question-title'>快捷问题</div>",
            unsafe_allow_html=True,
        )

        for row_start in range(0, len(EXAMPLE_QUESTIONS), 2):
            cols = st.columns(2)
            for offset, question_item in enumerate(
                EXAMPLE_QUESTIONS[row_start: row_start + 2]
            ):
                with cols[offset]:
                    if st.button(
                        question_item,
                        key=f"chat_example_submit_{row_start}_{offset}",
                        use_container_width=True,
                    ):
                        _submit_chat_question(question_item)

    default_question = st.session_state.get("selected_question", "")
    question = st.text_area(
        "输入业务问题",
        value=default_question,
        key="chat_question_input",
        height=90,
        placeholder="例如：查看月度销售趋势。下一轮可以继续问：那哪个州最高？",
        label_visibility="collapsed",
    )

    if st.button("发送并分析", type="primary", use_container_width=True):
        _submit_chat_question(question)


if __name__ == "__main__":
    run_dashboard()
