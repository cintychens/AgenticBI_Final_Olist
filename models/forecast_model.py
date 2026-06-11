from prophet import Prophet
import pandas as pd

from utils.db import run_query


def forecast_sales(periods=6):
    sql = """
    SELECT
        DATE_SUB(
            DATE(o.order_purchase_timestamp),
            INTERVAL WEEKDAY(o.order_purchase_timestamp) DAY
        ) AS ds,
        SUM(oi.price) AS y
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status <> 'canceled'
      AND o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp < '2018-09-01'
    GROUP BY ds
    ORDER BY ds
    """

    df = run_query(sql)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds")

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
    )

    model.fit(df)

    future = model.make_future_dataframe(
        periods=periods,
        freq="W",
    )

    forecast = model.predict(future)
    forecast = forecast.merge(
        df[["ds", "y"]],
        on="ds",
        how="left",
    )
    forecast["is_forecast"] = forecast["y"].isna()

    return forecast[
        [
            "ds",
            "y",
            "yhat",
            "yhat_lower",
            "yhat_upper",
            "is_forecast",
        ]
    ]
