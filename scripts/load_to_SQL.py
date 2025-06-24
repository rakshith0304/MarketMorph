import sqlite3
import pandas as pd

# Load your data
amazon_df = pd.read_csv("data/ecommerce/amazon_products.csv")
reddit_df = pd.read_csv("data/social/reddit_electronics_mentions.csv")

# Connect to SQLite (creates DB if it doesn't exist)
conn = sqlite3.connect("marketmorph.db")
cursor = conn.cursor()

# Create Products Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    price REAL,
    rating REAL,
    review_count INTEGER,
    url TEXT,
    keyword TEXT
)
''')

# Create Mentions Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT,
    post_text TEXT,
    subreddit TEXT,
    upvotes INTEGER,
    created TEXT,
    sentiment_score REAL,
    sentiment_label TEXT
)
''')

# Insert data from pandas
amazon_df.to_sql("products", conn, if_exists="replace", index=False)
reddit_df.to_sql("mentions", conn, if_exists="replace", index=False)

conn.commit()
conn.close()

print(":)))))))))  Data loaded into marketmorph.db")
