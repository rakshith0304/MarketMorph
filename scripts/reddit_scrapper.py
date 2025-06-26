import praw
import pandas as pd
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="marketmorph" 
)

# Load Amazon product names and get unique names
amazon_df = pd.read_csv("data/ecommerce/amazon_products.csv")
product_names = amazon_df["name"].dropna().unique().tolist()

# Subreddits to search
subreddits = ["technology", "gadgets", "headphones", "buildapc", "apple", "Android", "buyitforlife"]

posts = []

for sub in subreddits:
    print(f"Searching subreddit: r/{sub}") # Added for better progress tracking
    for product in product_names:
        print(f"  Searching for product: {product[:60]}...")  # Print first 60 chars for readability
        try: # Added error handling for potential subreddit not found or other issues
            for submission in reddit.subreddit(sub).search(product, limit=20):
                posts.append({
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "subreddit": sub,
                    "product_name": product,
                    "upvotes": submission.score,
                    "num_comments": submission.num_comments,
                    "author": str(submission.author),
                    "created": dt.datetime.fromtimestamp(submission.created_utc),
                })
        except Exception as e:
            print(f"  Error searching r/{sub} for {product[:60]}: {e}")
            continue 
df = pd.DataFrame(posts)


os.makedirs("data/social", exist_ok=True)

df.to_csv("data/social/reddit_electronics_mentions.csv", index=False)

print(":)))))))))  Reddit data saved!")