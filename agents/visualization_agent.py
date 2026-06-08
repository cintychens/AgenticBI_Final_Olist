import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import pandas as pd

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
            title="Payment Type × Installments Heatmap"
        )

        fig.update_layout(
            xaxis_title="Payment Installments",
            yaxis_title="Payment Type"
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
            title="Sales by State"
        )

        return fig

    # 品类销售柱状图
    elif "product_category" in columns and "total_gmv" in columns:

        fig = px.bar(
            df,
            x="product_category",
            y="total_gmv",
            title="Category Sales Ranking"
        )

        return fig

    # 支付方式频率柱状图
    elif "payment_type" in columns and "total_transactions" in columns:

        fig = px.bar(
            df,
            x="payment_type",
            y="total_transactions",
            title="Payment Method Frequency",
            text="total_transactions"
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
            title="Average Delivery Days by State"
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
            title="Seller Performance"
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

    fig = go.Figure()

    # 历史销售

    fig.add_trace(
        go.Scatter(
            x=history["ds"],
            y=history["yhat"],
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
            x=future["ds"],
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
            x=future["ds"],
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
            x=future["ds"],
            y=future["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",

            fillcolor="rgba(255,165,0,0.35)",

            name="Confidence Interval"
        )
    )

    fig.add_vline(

        x=history["ds"].max(),

        line_width=1,

        line_dash="dash",

        line_color="black"
    )

    fig.update_layout(

        title="Prophet Sales Forecast",

        xaxis_title="Month",

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
                {
                    "name": "forecast",
                    "figure": forecast_fig
                }
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
                {
                    "name": query_name,
                    "figure": fig
                }
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