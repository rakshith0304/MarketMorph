# MarketMorph: Trend Analysis of Electronics from Amazon + Reddit

MarketMorph is a production-ready pipeline that scrapes electronics product data from Amazon and public opinion from Reddit, processes it, and outputs clean, structured CSV files for visualization or analysis.

---

## What It Does

This Python script:
- Scrapes Amazon for product listings using any list of keywords (e.g., "smartwatch", "robot vacuum", etc.)
- Searches Reddit across relevant subreddits for mentions of those products
- Applies NLP sentiment analysis (using VADER) to Reddit titles
- Outputs 3 clean CSVs:
  - `amazon_products.csv` — list of products with price, rating, category
  - `reddit_raw.csv` — raw Reddit mentions
  - `reddit_mentions.csv` — sentiment-processed Reddit mentions

---

## How to Use

1. Clone the repo or download `main_pipeline.py`.
2. Set your Reddit API credentials in a `.env` file:
