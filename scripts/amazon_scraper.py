import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_amazon_products(keyword, num_pages=5):
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

            results.append({
                "name": name.text.strip() if name else None,
                "price": price_whole.text.strip().replace(",", "") if price_whole else None,
                "rating": rating.text.strip() if rating else None,
                "review_count": review_count.text.strip() if review_count else None,
                "category": keyword,
            })

        time.sleep(random.uniform(2, 5))  # polite delay

    df = pd.DataFrame(results)
    df.dropna(subset=["name", "price"], inplace=True)
    return df

if __name__ == "__main__":
    keywords = [
    "wireless earbuds",
    "smartphone",
    "laptop",
    "smart watch",
    "bluetooth speaker",
    "gaming mouse",
    "4k tv",
    "noise cancelling headphones",
    "external hard drive",
    "portable charger",
    "drone",
    "smart home hub",
    "mechanical keyboard",
    "fitness tracker",
    "action camera",
    "robot vacuum",
    "wifi router",
    "tablet",
    "video doorbell",
    "gaming headset"
]
    full_data = pd.DataFrame()

    for kw in keywords:
        print(f"Scraping Amazon for: {kw}")
        df = get_amazon_products(kw)
        full_data = pd.concat([full_data, df], ignore_index=True)

    full_data.to_csv("data/ecommerce/amazon_products.csv", index=False)
    print("Amazon data saved.")
