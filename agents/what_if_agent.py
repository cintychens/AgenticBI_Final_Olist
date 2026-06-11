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

    current_score = round(
        float(df["avg_review_score"].mean()),
        2,
    )

    sellers_to_remove = (
        df.sort_values(
            by="avg_review_score",
            ascending=True,
        )
        .head(20)
    )

    removed_seller_ids = set(sellers_to_remove["seller_id"])
    filtered_df = df[~df["seller_id"].isin(removed_seller_ids)]
    removed_sellers = len(sellers_to_remove)
    threshold = float(sellers_to_remove["avg_review_score"].max())

    improved_score = round(
        float(filtered_df["avg_review_score"].mean()),
        2,
    )

    improvement = round(
        improved_score - current_score,
        2,
    )

    return {
        "current_score": current_score,
        "improved_score": improved_score,
        "improvement": improvement,
        "removed_sellers": removed_sellers,
        "threshold": round(threshold, 2),
        "scenario": "Top 20 high-negative-review sellers removal",
        "removed_seller_ids": list(removed_seller_ids),
    }
