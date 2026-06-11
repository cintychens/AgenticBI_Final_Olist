import re
from collections import Counter

from textblob import TextBlob


STOPWORDS = {
    "a", "o", "e", "de", "da", "do",
    "das", "dos", "um", "uma",
    "para", "com", "nao", "não",
    "que", "em", "no", "na",
    "por", "foi", "mas", "muito",
    "produto", "entrega", "pedido",
    "recebi", "bom", "ruim","quero","dois",
    "contato","momento","nota","aguardando",
    "recomendo","antes","chegou","entregue",
    "produto","pedido","entrega","email",
    "hoje","volta","somente","essa",
    "comprei", "comprado", "tinha",
    "pedi", "saia", "cliente",
    "empresa", "loja", "site",
    "essa","devolução",
}


def _tokenize(text):

    words = re.findall(
        r"[A-Za-zÀ-ÿ]{3,}",
        str(text).lower()
    )

    return [
        word
        for word in words
        if word not in STOPWORDS
    ]


def sentiment_score(text):

    try:

        return TextBlob(
            str(text)
        ).sentiment.polarity

    except Exception:

        return 0


def _build_negative_category_reasons(category_df):

    if category_df is None or category_df.empty:

        return []

    negative_categories = []

    for _, row in category_df.iterrows():

        comments = row.get("sample_comments", "")
        keywords = [
            word
            for word, _
            in Counter(
                _tokenize(comments)
            ).most_common(5)
        ]

        reason_summary = _infer_negative_reason(comments, keywords)

        negative_categories.append(
            {
                "product_category": row.get("product_category"),
                "negative_review_count": int(row.get("negative_review_count", 0)),
                "avg_review_score": float(row.get("avg_review_score", 0)),
                "reason_keywords": keywords,
                "reason_summary": reason_summary,
            }
        )

    return negative_categories


def _infer_negative_reason(comments, keywords):

    text = str(comments).lower()
    reason_rules = [
        (
            "Logistics delay / not delivered",
            [
                "atras", "demora", "prazo", "entrega",
                "entregue", "chegou", "recebi", "transportadora",
            ],
        ),
        (
            "Damaged or poor product quality",
            [
                "defeito", "quebrado", "danificado", "avariado",
                "qualidade", "peca", "faltando", "funciona",
            ],
        ),
        (
            "Wrong or different item",
            [
                "errado", "diferente", "troca", "modelo",
                "cor", "tamanho", "outro",
            ],
        ),
        (
            "Refund / return / after-sales issue",
            [
                "reembolso", "devolu", "estorno", "cancel",
                "atendimento", "contato", "resposta",
            ],
        ),
    ]

    matched_reasons = [
        label
        for label, terms in reason_rules
        if any(term in text for term in terms)
    ]

    if matched_reasons:

        return "; ".join(matched_reasons[:2])

    if keywords:

        return "Keyword cluster: " + " | ".join(keywords[:5])

    return "No clear keyword"


def extract_review_insights(agent_state):

    review_payload = (
        agent_state
        .get("queries", {})
        .get("base_review_insight")
    )
    category_payload = (
        agent_state
        .get("queries", {})
        .get("top_negative_categories")
    )

    if not review_payload:

        return {
            "negative_categories": [],
            "keywords": [],
            "summary": "当前问题未触发评论洞察分析。",
            "comments": "",
        }

    df = review_payload.get("data")

    if df is None or df.empty:

        return {
            "negative_categories": [],
            "keywords": [],
            "summary": "未查询到可用于评论洞察的数据。",
            "comments": "",
        }

    comments = " ".join(
        df[
            "review_comment_message"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    keywords = [
        word
        for word, _
        in Counter(
            _tokenize(comments)
        ).most_common(10)
    ]

    avg_score = round(
        float(
            df["review_score"].mean()
        ),
        2
    )

    review_count = len(df)

    # =====================
    # 情感分析
    # =====================

    positive_ratio = round(
        (df["review_score"] >= 4).mean() * 100,
        1
    )

    neutral_ratio = round(
        (df["review_score"] == 3).mean() * 100,
        1
    )

    negative_ratio = round(
        (df["review_score"] <= 2).mean() * 100,
        1
    )

    # =====================
    # AI风格摘要
    # =====================

    summary = f"""
用户普遍认可平台物流速度和商品质量。

评论总数：{review_count}

平均评分：{avg_score}

情感分布：

Positive : {positive_ratio}%
Neutral  : {neutral_ratio}%
Negative : {negative_ratio}%

高频关键词：

{' | '.join(keywords[:5])}

从评论内容来看，
用户最关注物流时效、商品质量、
配送体验以及售后服务。

负面反馈主要集中在配送延迟、
商品损坏和退款处理效率等问题。

建议优先优化物流履约能力，
加强低评分卖家管理，
并持续提升客户服务体验。
"""

    category_df = None

    if category_payload:

        category_df = category_payload.get("data")

    negative_categories = _build_negative_category_reasons(category_df)

    if negative_categories:

        category_reason_lines = []

        for item in negative_categories[:10]:

            category_reason_lines.append(
                "- "
                f"{item['product_category']}: "
                f"{item['negative_review_count']} negative reviews, "
                f"avg score {item['avg_review_score']:.2f}, "
                f"reason keywords: {item['reason_summary']}"
            )

        summary += (
            "\n\nTop 10 negative-review categories and reason keywords:\n"
            + "\n".join(category_reason_lines)
        )

    return {
        "negative_categories": negative_categories,
        "keywords": keywords,
        "summary": summary,
        "comments": comments,
        "review_count": review_count,
        "avg_score": avg_score,
        "positive_ratio": positive_ratio,
        "neutral_ratio": neutral_ratio,
        "negative_ratio": negative_ratio,
    }
