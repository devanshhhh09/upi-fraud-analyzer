import json
import time
import requests
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

SUBREDDITS = [
    "india",
    "personalfinanceindia",
    "LegalAdviceIndia",
    "IndiaInvestments",
]

SEARCH_QUERIES = [
    "UPI fraud",
    "UPI scam",
    "paytm scam",
    "phonepe fraud",
    "google pay scam",
    "OTP fraud",
    "QR code scam",
    "online payment fraud",
]


class RedditScraper:
    """
    Scrapes Reddit posts about UPI fraud using
    the public JSON API — no API key required.
    """

    HEADERS = {
        "User-Agent": "UPIFraudResearch/1.0 (academic project; contact: research@example.com)"
    }

    def __init__(self):
        self.output_dir = config.RAW_DIR / "reddit"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def search_subreddit(self, subreddit: str, query: str, limit: int = 25) -> list[dict]:
        """Search a subreddit for posts matching a query."""
        url = (
            f"https://www.reddit.com/r/{subreddit}/search.json"
            f"?q={query.replace(' ', '+')}&restrict_sr=1&sort=relevance&limit={limit}"
        )

        try:
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            posts = data.get("data", {}).get("children", [])

            results = []
            for post in posts:
                p = post.get("data", {})

                # Skip posts with no meaningful text
                text = p.get("selftext", "").strip()
                if len(text) < 50:
                    continue

                results.append({
                    "title": p.get("title", ""),
                    "description": text,
                    "date": str(p.get("created_utc", "")),
                    "url": "https://reddit.com" + p.get("permalink", ""),
                    "score": p.get("score", 0),
                    "source": f"Reddit r/{subreddit}",
                    "query": query,
                })

            logger.info(
                f"r/{subreddit} + '{query}': {len(results)} posts"
            )
            time.sleep(2)  # Reddit rate limit: be polite
            return results

        except Exception as e:
            logger.error(f"Reddit scrape failed for r/{subreddit}: {e}")
            return []

    def run(self, max_posts: int = 200) -> list[dict]:
        """Scrape all subreddits and queries."""
        all_posts = []
        seen_urls = set()

        for subreddit in SUBREDDITS:
            for query in SEARCH_QUERIES:
                posts = self.search_subreddit(subreddit, query)

                for post in posts:
                    if post["url"] in seen_urls:
                        continue
                    seen_urls.add(post["url"])
                    all_posts.append(post)

                if len(all_posts) >= max_posts:
                    break
            if len(all_posts) >= max_posts:
                break

        # Save output
        output_path = config.RAW_DIR / "reddit_posts.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Reddit scraping complete. "
            f"{len(all_posts)} posts saved to {output_path}"
        )
        return all_posts


if __name__ == "__main__":
    scraper = RedditScraper()
    posts = scraper.run(max_posts=100)
    print(f"\nCollected {len(posts)} posts")
    if posts:
        print("\nSample post:")
        print(f"  Title: {posts[0]['title']}")
        print(f"  Source: {posts[0]['source']}")
        print(f"  Text preview: {posts[0]['description'][:200]}...")