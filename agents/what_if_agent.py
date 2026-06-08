from utils.db import run_query


def seller_removal_simulation():

    sql = """
    SELECT
        seller_id,
        avg_review_score
    FROM mv_seller_perf
    WHERE avg_review_score IS NOT NULL
    """

    df = run_query(sql)

    if df.empty:

        return None

    # 当前平台平均评分

    current_score = round(
        float(
            df["avg_review_score"].mean()
        ),
        2
    )

    # =====================
    # 找出评分最低10%的卖家
    # =====================

    threshold = (
        df["avg_review_score"]
        .quantile(0.10)
    )

    filtered_df = df[
        df["avg_review_score"]
        > threshold
    ]

    removed_sellers = (
        len(df) -
        len(filtered_df)
    )

    # =====================
    # 优化后评分
    # =====================

    improved_score = round(
        float(
            filtered_df[
                "avg_review_score"
            ].mean()
        ),
        2
    )

    improvement = round(
        improved_score -
        current_score,
        2
    )

    return {

        "current_score":
            current_score,

        "improved_score":
            improved_score,

        "improvement":
            improvement,

        "removed_sellers":
            removed_sellers,

        "threshold":
            round(
                float(threshold),
                2
            )

    }