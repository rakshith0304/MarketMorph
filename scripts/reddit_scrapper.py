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

# Keywords related to electronics
keywords = ["airpods", "smartwatch", "drone", "oled tv", "ps5", "gaming laptop"]

# Subreddits to search
subreddits = ["technology", "gadgets", "headphones", "buildapc", "apple", "Android", "buyitforlife"]

posts = []

for sub in subreddits:
    print(f"Searching subreddit: r/{sub}") # Added for better progress tracking
    for keyword in keywords:
        print(f"  Searching for keyword: {keyword}") # Added for better progress tracking
        try: # Added error handling for potential subreddit not found or other issues
            for submission in reddit.subreddit(sub).search(keyword, limit=200):
                posts.append({
                    "title": submission.title,
                    "text": submission.selftext,
                    "subreddit": sub,
                    "keyword": keyword,
                    "upvotes": submission.score,
                    "created": dt.datetime.fromtimestamp(submission.created_utc),
                    "url": submission.url
                })
        except Exception as e:
            print(f"  Error searching r/{sub} for {keyword}: {e}")
            continue 
df = pd.DataFrame(posts)


os.makedirs("data/social", exist_ok=True)

df.to_csv("data/social/reddit_electronics_mentions.csv", index=False)
print("✅ Reddit data saved!")

## testinf commit