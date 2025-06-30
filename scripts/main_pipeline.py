# === IMPORTS ===
import datetime as dt
import os
import random
import re
import requests
import time

import pandas as pd
import praw
import spacy
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# === GLOBAL SETUP ===

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

nlp = spacy.load("en_core_web_sm")
load_dotenv()

# Initialize Reddit API client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent="marketmorph"
)

# === FUNCTIONS ===

def get_amazon_products(keyword, num_pages=5):
    """
    Scrapes product listings from Amazon based on a search keyword.
    Returns a cleaned pandas DataFrame.
    """
    results = []

    for page in range(1, num_pages + 1):
        url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}&page={page}"
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")

        for product in soup.select("div.s-main-slot div.s-result-item"):
            name = product.select_one("h2 span")
            price_whole = product.select_one("span.a-price-whole")
            rating = product.select_one("span.a-icon-alt")
            review_count = product.select_one("span.a-size-base")

            price = price_whole.text.strip().replace(",", "") if price_whole else None
            if price and price.endswith('.'):
                price = price[:-1]

            results.append({
                "product_name": name.text.strip() if name else None,
                "price": price,
                "rating": float(rating.text.strip().split()[0]) if rating and re.match(r'^\d+(\.\d+)?', rating.text.strip()) else None,
                "review_count": review_count.text.strip() if review_count else None,
                "category": keyword,
            })

        time.sleep(random.uniform(2, 5))  # polite delay to avoid blocking

    df = pd.DataFrame(results)
    df.dropna(subset=["product_name", "price"], inplace=True)
    return df


def hybrid_clean_title(title):
    """
    Cleans an Amazon product title to extract a simplified, core product name
    (typically brand + model/main product type).
    Prioritizes identifying brand and model information while removing common descriptive noise.

    Args:
        title (str): The original Amazon product title string.

    Returns:
        str: The cleaned and simplified product title. Returns an empty string
             if the input is not a valid string or is empty.
    """
    if not isinstance(title, str) or not title.strip():
        return ""

    original_title = title.strip()
    cleaned_title = original_title.lower()

    # 1. Remove content within parentheses () and square brackets []
    # These often contain secondary details like color, size, compatibility, or year.
    cleaned_title = re.sub(r"\(.*?\)", "", cleaned_title)
    cleaned_title = re.sub(r"\[.*?\]", "", cleaned_title)

    # 2. Remove common Amazon noise phrases, descriptive words, and units.
    # The patterns are designed to match whole words or specific phrases.
    noise_patterns = [
        r"\bnewest\b", r"\bversion\b", r"\bmodel\b", r"\bseries\b",
        r"\bpack of \d+\b", r"\bset of \d+\b", r"\b(pk|count) of \d+\b",
        r"\bunlocked\b", r"\bunlocked smartphone\b", r"\bofficial\b",
        r"\b(us|international) version\b", r"\b(20\d{2})\b", # Years like (2022)
        r"\bfor \w+\s?\w*\b", # 'for iphone', 'for samsung', 'for car' etc.
        r"\bcompatible with\b", r"\bcase for\b", r"\bprotector\b",
        r"\bscreen\b", r"\bcharger\b", r"\bcable\b", r"\badapter\b",
        r"\b(mount|stand)\b", r"\bhousing\b", r"\baccessory\b",
        # Common colors. Keep if part of a brand/model (handled by later logic).
        r"\b(black|white|blue|red|green|silver|gold|grey|pink|purple|phantom|titanium|starlight|midnight|graphite|alpine|sierra|rose|platinum)\b",
        r"\d{2,3}(?:gb|tb|mb)\b", # Storage units with numbers like 128GB, 2TB
        r"\b(gb|tb|mb)\b", # Generic storage units
        r"\b(pc|pcs)\b", # Pieces (e.g., 2 Pcs)
        r"\bphone\b", r"\bsmartphone\b", r"\bdevice\b", r"\btablet\b",
        r"\boverview\b", r"\bfeatures\b", r"\b(high|premium) quality\b",
        r"\b(original|authentic)\b", r"\b(replacement|spare)\b",
        r"\bkit\b", r"\btool\b", r"\bsupplies\b", r"\bparts?\b",
        r"\bcombo\b", r"\bdeal\b", r"\bbundle\b",
        r"\b(hd|fhd|uhd|4k|8k)\b", # Display resolutions
        r"\bwireless\b", r"\bwired\b", r"\bbluetooth\b", r"\bwi-fi\b",
        r"\baluminum\b", r"\bsilicone\b", r"\btpu\b", r"\bglass\b", r"\bleather\b", # Materials
        r"\bcamera\b", r"\b(front|rear)\b", r"\bdual camera\b",
        r"\bdisplay\b", r"\b(lcd|oled|amoled)\b", r"\btouchscreen\b",
        r"\bslim\b", r"\bdurable\b", r"\bheavy duty\b", r"\bwaterproof\b",
        r"\bnew\b", r"\bquick charge\b", r"\bfast charge\b", r"\bwall charger\b",
        r"\bgen\s?\d+\b", # Gen 1, Gen 2 (e.g., "Fire HD 10 Gen 11")
        r"\bstorage\b", r"\bmemory\b",
        r"\b(car|auto|vehicle)\b", # Car-related descriptions
        r"\b(universal|multi-purpose)\b",
        r"\boverall\b", r"\bperformance\b", r"\bdesign\b",
        r"\bstyle\b", r"\bcolor\b", r"\bmaterial\b",
        r"\b(fast|quick)\b", r"\b(super|ultra)\b",
    ]
    for pattern in noise_patterns:
        cleaned_title = re.sub(pattern, "", cleaned_title)

    # Remove any remaining multiple spaces and strip leading/trailing spaces
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()

    doc = nlp(cleaned_title)

    # 3. Extract core terms: Brand, Model, and Key Product Type
    final_terms = []
    seen_lower = set() # To keep track of terms already added (case-insensitive)

    # Prioritize capitalized words at the beginning of the ORIGINAL title as potential brands.
    # This helps preserve original brand casing (e.g., "SAMSUNG" vs "Samsung").
    original_tokens = original_title.split()
    brand_candidate = ""
    if original_tokens and original_tokens[0].istitle() and len(original_tokens[0]) > 1:
        brand_candidate = original_tokens[0]
        # Check for multi-word brands (e.g., "Google Pixel")
        if len(original_tokens) > 1 and original_tokens[1].istitle() and len(original_tokens[1]) > 1:
            brand_candidate += " " + original_tokens[1]
            if len(original_tokens) > 2 and original_tokens[2].istitle() and len(original_tokens[2]) > 1:
                 brand_candidate += " " + original_tokens[2]

    # Add brand if found and not already present (case-insensitive)
    if brand_candidate and brand_candidate.lower() not in seen_lower:
        final_terms.append(brand_candidate)
        seen_lower.add(brand_candidate.lower())

    # Process tokens from the cleaned title for model numbers and product types
    significant_tokens = []
    # Define a regex for common model number patterns (e.g., "M1", "S22", "iPhone13", "735")
    model_regex = r"^(?:[A-Za-z]{1,3})?\d+[A-Za-z0-9-]*$|^[A-Za-z]{2,}[0-9]+[A-Za-z]*$"

    for token in doc:
        # Filter out stopwords and punctuation that might have survived previous cleaning
        if not token.is_stop and not token.is_punct:
            token_text = token.text

            # Avoid adding terms that are clearly just noise from the predefined patterns.
            is_noise_word = False
            for noise_p in noise_patterns:
                if re.search(r'\b' + re.escape(token_text) + r'\b', noise_p):
                    is_noise_word = True
                    break
            if is_noise_word:
                continue

            # Prioritize terms that match model number patterns
            if re.match(model_regex, token_text):
                if token_text.lower() not in seen_lower:
                    significant_tokens.append(token_text)
                    seen_lower.add(token_text.lower())
            # Or terms that are proper nouns or look like important product names (e.g., "Galaxy", "Pixel", "AirPods", "Ultra")
            elif token.pos_ == "PROPN" or (token_text.istitle() and len(token_text) > 1) or \
                 (token_text.upper() == token_text and len(token_text) > 1): # Acronyms like "USB", "5G", "LTE"
                if token_text.lower() not in seen_lower:
                    significant_tokens.append(token_text)
                    seen_lower.add(token_text.lower())
            # Fallback for important nouns (e.g., "headset", "earbuds", "speaker")
            elif token.pos_ == "NOUN" and len(token_text) > 1 and token_text.lower() not in seen_lower:
                significant_tokens.append(token_text)
                seen_lower.add(token_text.lower())
                
    # Reconstruct final_terms, ensuring brand is first and then other significant terms
    # Filtering out duplicates and terms already covered by the brand
    temp_final_terms = []
    if brand_candidate:
        temp_final_terms.append(brand_candidate)
        
    for term in significant_tokens:
        # Only add if not a duplicate and not part of the already added brand (case-insensitive)
        if term.lower() not in [t.lower() for t in temp_final_terms]:
            temp_final_terms.append(term)
    final_terms = temp_final_terms

    # Post-processing for final capitalization and formatting
    result_tokens = []
    for token_text in final_terms:
        # Preserve original capitalization for words that were originally entirely uppercase (e.g., USB, 5G)
        # This checks if the exact-cased token exists in the original title and is uppercase.
        original_idx = original_title.lower().find(token_text.lower())
        if original_idx != -1 and original_title[original_idx : original_idx + len(token_text)].isupper():
            result_tokens.append(token_text.upper())
        # Capitalize the first letter if it's a title-cased word or a proper noun
        elif token_text.istitle() or nlp(token_text)[0].pos_ == "PROPN":
            result_tokens.append(token_text.capitalize())
        else:
            # Default to capitalizing the first letter
            result_tokens.append(token_text.capitalize())

    result = " ".join(result_tokens).strip()

    # Final length check to prevent overly long titles.
    # Truncates to the last full word before the limit.
    if len(result) > 70: # Arbitrary limit for a "clean" title
        result = result[:70].rsplit(' ', 1)[0] + "..." if ' ' in result[:70] else result[:70] + "..."

    # If no useful terms were extracted, fall back to the first few original words
    # or a truncated version of the original title.
    if not result:
        fallback_tokens = [
            tok.text for tok in nlp(original_title)
            if not tok.is_stop and not tok.is_punct and len(tok.text) > 1
        ][:5] # Take up to 5 significant words
        result = " ".join([t.capitalize() for t in fallback_tokens if t]).strip()
        if not result:
            result = original_title[:50].strip() # Last resort, just truncate original

    return result



def get_sentiment_score(text):
    """
    Returns compound sentiment score using VADER.
    """
    try:
        return analyzer.polarity_scores(str(text))["compound"]
    except:
        return 0.0


def get_sentiment_label(score):
    """
    Converts a VADER compound score into a sentiment label.
    """
    if score >= 0.2:
        return "positive"
    elif score <= -0.2:
        return "negative"
    else:
        return "neutral"

# === MAIN SCRIPT ===
if __name__ == "__main__":
    # List of product keywords to search on Amazon
    keywords = [
    "Smartphones",
    "Smart TVs",
    "Refrigerators",
    "Bluetooth Speakers",
    "Laptops",
    "Headphones",
    "Smartwatches",
    "Gaming Consoles",
    "Wireless Earbuds",
    "Tablets",
    "Monitors",
    "Printers",
    "Air Conditioners",
    "Microwaves",
    "Washing Machines",
    "Robot Vacuums",
    "Drones",
    "Projectors",
    "Fitness Trackers",
    "Power Banks"
]

    amazon_df = pd.DataFrame()

    # Scrape and process Amazon products
    for kw in keywords:
        print(f"Scraping Amazon for: {kw}")
        df = get_amazon_products(kw)
        amazon_df = pd.concat([amazon_df, df], ignore_index=True)

    # Clean Amazon data
    amazon_df["product_name"] = amazon_df["product_name"].apply(hybrid_clean_title)
    amazon_df["review_count"] = pd.to_numeric(amazon_df["review_count"], errors="coerce")
    amazon_df.dropna(subset=["rating", "review_count"], inplace=True)
    amazon_df["review_count"] = amazon_df["review_count"].astype(int)
    amazon_df.to_csv("data/amazon_products.csv", index=False)
    print(":)))))))))  Amazon data saved.")

    # Prepare for Reddit scraping
    product_names = amazon_df["product_name"].dropna().unique().tolist()
    subreddits = [
    "BuyItForLife",
    "buildapcsales",
    "techsupport",
    "AskElectronics",
    "hardware",
    "gadgets",
    "smarthome",
    "homeautomation",
    "diyelectronics",
    "electronics",
]
    posts = []

    # Search Reddit for product mentions
    for sub in subreddits:
        print(f"Searching subreddit: r/{sub}")
        for product in product_names:
            print(f"  Searching for product: {product[:60]}...")
            try:
                for submission in reddit.subreddit(sub).search(product, limit=20):
                    posts.append({
                        "title": submission.title,
                        "subreddit": sub,
                        "product_name": product,
                        "upvotes": submission.score,
                        "num_comments": submission.num_comments,
                        "date": dt.datetime.fromtimestamp(submission.created_utc),
                    })
            except Exception as e:
                print(f"  Error searching r/{sub} for {product[:60]}: {e}")
                continue

    reddit_df = pd.DataFrame(posts)
    reddit_df.to_csv("data/raw/reddit_raw.csv", index=False)
    print(":)))))))))  Reddit data saved!")

    # === NLP SENTIMENT ANALYSIS ===
    print("Starting NLP sentiment analysis...")

    # Clean title for compatibility
    reddit_df["title"] = (
        reddit_df["title"]
        .astype(str)
        .str.replace(r"[\n\r\t]+", " ", regex=True)
        .str.replace('"', "'")
        .str.replace(",", " ")
        .str.strip()
    )

    # Ensure date format
    if "date" in reddit_df.columns:
        reddit_df["date"] = pd.to_datetime(reddit_df["date"], errors="coerce")

    # Apply sentiment scoring
    analyzer = SentimentIntensityAnalyzer()
    reddit_df["sentiment_score"] = reddit_df["title"].apply(get_sentiment_score)
    reddit_df["sentiment_label"] = reddit_df["sentiment_score"].apply(get_sentiment_label)
    reddit_df["sentiment_score"] = pd.to_numeric(reddit_df["sentiment_score"], errors='coerce')

    # Remove unnecessary columns
    reddit_df.drop(columns=["title", "subreddit"], inplace=True)

    # Save final output
    reddit_df.to_csv("data/reddit_mentions.csv", index=False, encoding="utf-8")
    print(":))))))))) Data cleaned and sentiment analysis completed.")
