import hashlib
import re
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import pandas as pd

CHART_OUTPUT_DIR = Path("outputs") / "charts" / "latest"
CHART_COLOR_SEQUENCE = [
    "#2563eb",
    "#16a34a",
    "#f97316",
    "#9333ea",
    "#dc2626",
    "#0891b2",
    "#ca8a04",
    "#4f46e5",
]

BRAZIL_STATE_COORDS = {

    "SP": (-23.55, -46.63),
    "RJ": (-22.90, -43.20),
    "MG": (-19.92, -43.94),
    "BA": (-12.97, -38.50),
    "PR": (-25.42, -49.27),
    "RS": (-30.03, -51.23),
    "SC": (-27.59, -48.55),
    "GO": (-16.68, -49.25),
    "PE": (-8.05, -34.88),
    "CE": (-3.73, -38.54),
    "PA": (-1.45, -48.49),
    "MT": (-15.60, -56.10),
    "MS": (-20.45, -54.61),
    "ES": (-20.31, -40.31),
    "DF": (-15.79, -47.88)
}


def _safe_chart_name(chart_name):
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", chart_name.strip())
    return safe_name.strip("_") or "chart"


def _apply_export_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1f2937"),
        colorway=CHART_COLOR_SEQUENCE,
    )

    fig.update_xaxes(
        gridcolor="#e5e7eb",
        zerolinecolor="#cbd5e1",
        linecolor="#cbd5e1",
        tickfont=dict(color="#475569"),
        title_font=dict(color="#475569"),
    )
    fig.update_yaxes(
        gridcolor="#e5e7eb",
        zerolinecolor="#cbd5e1",
        linecolor="#cbd5e1",
        tickfont=dict(color="#475569"),
        title_font=dict(color="#475569"),
    )

    for index, trace in enumerate(fig.data):
        fallback_color = CHART_COLOR_SEQUENCE[index % len(CHART_COLOR_SEQUENCE)]

        if trace.type in {"scatter", "bar"}:
            marker = getattr(trace, "marker", None)
            if marker is not None:
                marker_color = getattr(marker, "color", None)
                if marker_color in {None, "#000", "#000000", "black"}:
                    trace.marker.color = fallback_color

            line = getattr(trace, "line", None)
            if line is not None:
                line_color = getattr(line, "color", None)
                if line_color in {None, "#000", "#000000", "black"}:
                    trace.line.color = fallback_color

    return fig


def _chart_file_key(chart_name, payload=None):
    if not payload:
        return chart_name

    view_name = payload.get("view") or "custom"
    sql_text = payload.get("sql") or ""
    signature_source = f"{chart_name}|{view_name}|{sql_text}"
    signature = hashlib.md5(signature_source.encode("utf-8")).hexdigest()[:8]

    return f"{chart_name}_{view_name}_{signature}"


def save_chart_file(fig, chart_name):
    CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_chart_name(chart_name)
    png_path = CHART_OUTPUT_DIR / f"{safe_name}.png"
    html_path = CHART_OUTPUT_DIR / f"{safe_name}.html"
    export_fig = _apply_export_theme(fig)

    try:
        if html_path.exists():
            html_path.unlink()
        export_fig.write_image(str(png_path), width=1400, height=800, scale=2)
        return str(png_path)
    except Exception as exc:
        if png_path.exists():
            png_path.unlink()
        export_fig.write_html(str(html_path), include_plotlyjs="cdn")
        print(f"[CHART SAVE WARNING] PNG export failed for {chart_name}: {exc}")
        print(f"[CHART SAVE WARNING] Saved interactive HTML instead: {html_path}")
        return str(html_path)


def _build_chart_payload(chart_name, fig, payload=None):
    file_key = _chart_file_key(chart_name, payload)

    return {
        "name": chart_name,
        "figure": fig,
        "file_path": save_chart_file(fig, file_key),
    }

def create_chart(df):

    columns = df.columns

    # 商品重量 vs 运费散点图
    if (
        "product_weight_g" in columns
        and "freight_value" in columns
        and "order_count" in columns
        and "order_status" in columns
    ):

        fig = px.scatter(
            df,
            x="product_weight_g",
            y="freight_value",
            size="order_count",
            color="order_status",
            title="Product Weight vs Freight Cost",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
            hover_data=[
                "order_count"
            ] 
        )

        fig.update_layout(
            xaxis_title="Product Weight (g)",
            yaxis_title="Freight Cost"
        )

        return fig

    # 支付方式 × 分期数热力图
    if (
        "payment_type" in columns
        and "payment_installments" in columns
        and "transaction_count" in columns
    ):
        matrix = df.pivot_table(
            index="payment_type",
            columns="payment_installments",
            values="transaction_count",
            aggfunc="sum",
            fill_value=0
        )

        fig = px.imshow(
            matrix,
            text_auto=True,
            aspect="auto",
            title="Payment Type × Installments Heatmap",
            color_continuous_scale=[
                "#eff6ff",
                "#bfdbfe",
                "#60a5fa",
                "#2563eb",
                "#1e3a8a",
            ],
        )

        fig.update_layout(
            xaxis_title="Payment Installments",
            yaxis_title="Payment Type"
        )
        fig.update_traces(
            textfont=dict(color="#1f2937")
        )

        return fig

    # 月度GMV趋势图
    elif "ym" in columns and "total_gmv" in columns:

        fig = px.line(
            df,
            x="ym",
            y="total_gmv",
            title="Monthly GMV Trend",
            markers=True
        )

        return fig

    # 州销售柱状图
    elif "customer_state" in columns and "total_gmv" in columns:

        fig = px.bar(
            df,
            x="customer_state",
            y="total_gmv",
            title="Sales by State",
            color="customer_state",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
        )

        return fig

    # 品类销售柱状图
    elif "product_category" in columns and "total_gmv" in columns:

        fig = px.bar(
            df,
            x="product_category",
            y="total_gmv",
            title="Category Sales Ranking",
            color="product_category",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
        )

        return fig

    # 支付方式频率柱状图
    elif "payment_type" in columns and "total_transactions" in columns:

        fig = px.bar(
            df,
            x="payment_type",
            y="total_transactions",
            title="Payment Method Frequency",
            text="total_transactions",
            color="payment_type",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
        )

        fig.update_layout(
            xaxis_title="Payment Type",
            yaxis_title="Transaction Count"
        )

        return fig

    # 配送表现柱状图
    elif "customer_state" in columns and "avg_delivery_days" in columns:

        fig = px.bar(
            df,
            x="customer_state",
            y="avg_delivery_days",
            title="Average Delivery Days by State",
            color="customer_state",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
        )

        return fig

    # 卖家绩效散点图
    elif "avg_review_score" in columns and "total_gmv" in columns:

        fig = px.scatter(
            df,
            x="total_gmv",
            y="avg_review_score",
            color="seller_state",
            size="total_orders",
            title="Seller Performance",
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
        )

        return fig

    return None

def create_forecast_chart(forecast):

    if forecast is None or forecast.empty:

        return None

    history = forecast[
        forecast["is_forecast"] == False
    ]

    future = forecast[
        forecast["is_forecast"] == True
    ]

    history_x = pd.to_datetime(history["ds"]).dt.to_pydatetime()
    future_x = pd.to_datetime(future["ds"]).dt.to_pydatetime()
    cutoff_date = pd.to_datetime(history["ds"].max()).to_pydatetime()

    fig = go.Figure()

    # 历史销售

    fig.add_trace(
        go.Scatter(
            x=history_x,
            y=history["y"] if "y" in history.columns else history["yhat"],
            mode="lines+markers",

            line=dict(
                color="blue",
                width=3
            ),

            name="Historical Sales"
        )
    )

    # 预测销售

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=future["yhat"],
            mode="lines+markers",

            line=dict(
                color="red",
                width=3
            ),

            name="Forecast Sales"
        )
    )

    # 置信区间上界

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=future["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    # 置信区间下界

    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=future["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",

            fillcolor="rgba(255,165,0,0.35)",

            name="Confidence Interval"
        )
    )

    fig.add_vline(

        x=cutoff_date,

        line_width=1,

        line_dash="dash",

        line_color="black"
    )

    fig.update_layout(

        title="Prophet Weekly Sales Forecast",

        xaxis_title="Week",

        yaxis_title="GMV",

        hovermode="x unified",

        height=600
    )

    return fig

def create_charts(queries, forecast=None):

    charts = []

    # Prophet预测图
    if forecast is not None:

        forecast_fig = create_forecast_chart(
            forecast
        )

        if forecast_fig is not None:

            charts.append(
                _build_chart_payload("forecast", forecast_fig)
            )

    # 其它图表
    for query_name, payload in queries.items():

        df = payload.get("data")

        if df is None:

            continue

        if query_name == "state_geo_map":

            fig = create_state_geo_map(df)

        # =====================
        # 好评词云
        # =====================

        elif query_name == "positive_wordcloud":

            fig = create_wordcloud(
                df,
                "Positive Review Keywords"
            )

        # =====================
        # 差评词云
        # =====================

        elif query_name == "negative_wordcloud":

            fig = create_wordcloud(
                df,
                "Negative Review Keywords"
            )

        # =====================
        # 普通图表
        # =====================

        else:

            fig = create_chart(df)

        if fig is not None:

            charts.append(
                _build_chart_payload(query_name, fig, payload)
            )

    print(
        "Charts Generated:",
        len(charts)
    )

    for chart in charts:

        print(
            chart["name"]
        )

    return charts

def create_wordcloud(
    df,
    title
):

    text = " ".join(
        df[
            "review_comment_message"
        ].astype(str)
    )

    if not text.strip():

        return None

    custom_stopwords = STOPWORDS.union(
        {

            # Portuguese common words
            "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas",
            "um", "uma", "uns", "umas",
            "para", "por", "com", "que",
            "foi", "não", "nao",
            "muito", "bem",

            # Pronouns
            "eu", "me", "mim",
            "meu", "minha",
            "meus", "minhas",

            # Common meaningless words
            "como",
            "tudo",
            "veio",
            "agora",
            "ainda",
            "até",
            "ate",
            "só",
            "so",
            "estou",
            "está",
            "esta",
            "pela",
            "pelo",
            "porque",
            "porém",
            "também",
            "tambem",
            "ter",
            "ser",
            "era",

            # Negative cloud noise
            "comprei",
            "comprado",
            "apena",
            "apenas",
            "mais",
            "mesmo",
            "outro",
            "outra",
            "duas",
            "nada",
            "pois",
            "quando",
            "sobre",
            "cliente",
            "empresa",
            "mercadoria",
            "unidade",

            # E-commerce neutral words
            "produto",
            "produtos",
            "pedido",
            "pedidos",
            "compra",
            "compras",
            "comprar",
            "loja",
            "lojas",
            "site",
            "entrega",
            "entregue",
            "entregou",
            "chegou",
            "recebi",
            "recebido",
            "prazo",
            "dia",
            "dias",

            # English fallback words
            "product",
            "products",
            "order",
            "orders",
            "delivery",
            "delivered",
            "received",
            "purchase",
            "store"
        }
    )

    wc = WordCloud(
        width=1200,
        height=600,

        background_color="white",

        stopwords=custom_stopwords,

        max_words=80,
        min_word_length=4,

        relative_scaling=0.3,

        collocations=False
    ).generate(text)

    fig = px.imshow(
        wc.to_array(),
        title=title
    )

    fig.update_xaxes(
        visible=False
    )

    fig.update_yaxes(
        visible=False
    )

    fig.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10
        )
    )

    return fig

def create_state_geo_map(df):

    df = df.copy()

    df["lat"] = df["customer_state"].map(
        lambda x: BRAZIL_STATE_COORDS.get(
            x,
            (None, None)
        )[0]
    )

    df["lon"] = df["customer_state"].map(
        lambda x: BRAZIL_STATE_COORDS.get(
            x,
            (None, None)
        )[1]
    )

    df = df.dropna(
        subset=["lat", "lon"]
    )

    fig = px.scatter_geo(

        df,

        lat="lat",

        lon="lon",

        size="total_orders",

        color="total_gmv",

        hover_name="customer_state",

        hover_data={
            "total_gmv": ":,.0f",
            "total_orders": True
        },

        scope="south america",

        title="Brazil Sales Distribution Map"
    )

    fig.update_geos(

        projection_type="mercator",

        fitbounds="locations",

        showcountries=True,

        showland=True,

        lataxis_range=[-35, 8],

        lonaxis_range=[-75, -30]
    )

    fig.update_layout(

        height=800,

        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10
        ),

        coloraxis_colorbar=dict(
            title="GMV"
        )
    )

    return fig
