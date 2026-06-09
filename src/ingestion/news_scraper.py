import json
import requests
import os
from datetime import datetime, timedelta
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

QUERIES = [
    "UPI fraud India",
    "UPI scam India",
    "digital payment fraud India",
    "PhonePe fraud",
    "Paytm scam",
    "Google Pay fraud India",
    "OTP fraud India",
    "QR code scam India",
    "cyber fraud arrest India",
    "online payment scam India",
]


class NewsAPIScraper:
    """
    Collects UPI fraud news articles using NewsAPI free tier.
    Free tier: 100 requests/day, articles from last 30 days.
    """

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        self.api_key = config.NEWS_API_KEY
        self.output_dir = config.RAW_DIR / "news"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            raise ValueError(
                "NEWS_API_KEY not found. "
                "Add it to your .env file: NEWS_API_KEY=your_key_here"
            )

    def search(self, query: str, days_back: int = 30) -> list[dict]:
        """Search for articles matching a query."""
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 100,
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                logger.warning(f"NewsAPI error for '{query}': {data.get('message')}")
                return []

            articles = data.get("articles", [])
            results = []

            for a in articles:
                # Combine title and description for richer text
                text = " ".join(filter(None, [
                    a.get("title", ""),
                    a.get("description", ""),
                    a.get("content", ""),
                ]))

                if len(text) < 50:
                    continue

                results.append({
                    "title": a.get("title", ""),
                    "description": text,
                    "date": a.get("publishedAt", ""),
                    "url": a.get("url", ""),
                    "source": f"NewsAPI:{a.get('source', {}).get('name', 'unknown')}",
                    "query": query,
                })

            logger.info(f"NewsAPI '{query}': {len(results)} articles")
            return results

        except Exception as e:
            logger.error(f"NewsAPI request failed for '{query}': {e}")
            return []

    def run(self, max_articles: int = 500) -> list[dict]:
        """Run all queries and combine results."""
        all_articles = []
        seen_urls = set()

        for query in QUERIES:
            articles = self.search(query)
            for article in articles:
                if article["url"] in seen_urls:
                    continue
                seen_urls.add(article["url"])
                all_articles.append(article)

            if len(all_articles) >= max_articles:
                break

        output_path = config.RAW_DIR / "news_articles.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)

        logger.info(f"NewsAPI complete. {len(all_articles)} articles → {output_path}")
        return all_articles


if __name__ == "__main__":
    scraper = NewsAPIScraper()
    articles = scraper.run()
    print(f"\nCollected {len(articles)} articles")
    if articles:
        print(f"\nSample article:")
        print(f"  Title:  {articles[0]['title']}")
        print(f"  Source: {articles[0]['source']}")
        print(f"  Text preview: {articles[0]['description'][:200]}...")
