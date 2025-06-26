import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load your data
reddit_df = pd.read_csv("data/social/reddit_electronics_mentions.csv")

# NLP Sentiment Analysis

analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(text):
    try:
        return analyzer.polarity_scores(str(text))["compound"]
    except:
        return 0.0

def get_sentiment_label(score):
    if score >= 0.2:
        return "positive"
    elif score <= -0.2:
        return "negative"
    else:
        return "neutral"

reddit_df["sentiment_score"] = reddit_df["selftext"].apply(get_sentiment_score)
reddit_df["sentiment_label"] = reddit_df["sentiment_score"].apply(get_sentiment_label)


reddit_df.to_csv("data/social/reddit_electronics_mentions.csv",index=False)
print(":))))))))) Data cleaned and sentiment analysis completed.")
