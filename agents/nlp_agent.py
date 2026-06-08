from textblob import TextBlob
from collections import Counter

from wordcloud import WordCloud


def analyze_review(text):

    sentiment = TextBlob(text)

    return sentiment.sentiment.polarity


def extract_top_words(texts, top_n=20):

    all_words = []

    stop_words = {
        "the", "and", "for", "with", "that",
        "this", "was", "are", "you", "have",
        "not", "but", "very", "from", "they",
        "will", "has", "had", "were"
    }

    for text in texts:

        if not text:
            continue

        words = str(text).lower().split()

        words = [
            w
            for w in words
            if len(w) > 2
            and w not in stop_words
        ]

        all_words.extend(words)

    counter = Counter(all_words)

    return counter.most_common(top_n)


def create_wordcloud(texts):

    text = " ".join(
        [
            str(t)
            for t in texts
            if t
        ]
    )

    if not text.strip():

        return None

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white"
    )

    wc.generate(text)

    return wc