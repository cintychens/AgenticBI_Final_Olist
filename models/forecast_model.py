from prophet import Prophet
import pandas as pd

from utils.db import run_query


def forecast_sales(periods=6):

    sql = """
    SELECT
        ym,
        total_gmv
    FROM mv_monthly_sales
    WHERE ym BETWEEN '2017-01' AND '2018-08'
    ORDER BY ym
    """

    df = run_query(sql)

    df = df.rename(
        columns={
            "ym": "ds",
            "total_gmv": "y"
        }
    )

    # 转日期
    df["ds"] = pd.to_datetime(df["ds"])

    # 按时间排序
    df = df.sort_values("ds")

    # Prophet模型
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False
    )

    model.fit(df)

    # 未来6个月
    future = model.make_future_dataframe(
        periods=periods,
        freq="MS"
    )

    forecast = model.predict(future)

    # 标记哪些是未来预测数据
    forecast["is_forecast"] = False

    forecast.loc[
        forecast.index >= len(df),
        "is_forecast"
    ] = True

    return forecast[
        [
            "ds",
            "yhat",
            "yhat_lower",
            "yhat_upper",
            "is_forecast"
        ]
]