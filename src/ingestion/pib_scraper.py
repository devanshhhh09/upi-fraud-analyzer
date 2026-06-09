import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from src.ingestion.base_scraper import BaseScraper
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

PIB_SEARCH_URL = (
    "https://pib.gov.in/AllRelease.aspx"
)

PIB_SEARCH_QUERIES = [
    "UPI fraud",
    "cyber fraud arrest",
    "online fraud",
    "digital payment fraud",
    "phishing UPI",
]


class PIBScraper(BaseScraper):
    """
    Scrapes Press Information Bureau press releases
    related to UPI and cyber fraud.

    Output: list of dicts with keys:
        title, date, description, url, source
    """

    def __init__(self):
        super().__init__(
            output_dir=config.RAW_DIR / "pib",
            delay_min=2.0,
            delay_max=4.0,
        )

    def scrape_search_page(self, query: str, page: int = 1) -> list[dict]:
        """Scrape one page of PIB search results for a query."""
        url = f"https://pib.gov.in/SearchReleaseAll.aspx?lang=1&kimage=14&searchterm={query.replace(' ', '+')}"
        html = self.fetch(url)

        if not html:
            logger.warning(f"No HTML returned for query: {query}")
            return []

        filename = f"pib_search_{query.replace(' ', '_')}_p{page}.html"
        self.save_raw(filename, html)

        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[dict]:
        """Extract article metadata from PIB search results page."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # PIB search results are in ContentDiv table rows
        rows = soup.find_all("div", class_=re.compile(r"(ContentDiv|search-result|press-release)"))

        if not rows:
            # Fallback: find all links with dates nearby
            rows = soup.find_all("li")

        for row in rows:
            try:
                title_tag = row.find("a")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag.get("href", "")

                if not link.startswith("http"):
                    link = "https://pib.gov.in" + link

                # Extract date if present
                date_text = ""
                date_tag = row.find(string=re.compile(r"\d{2}/\d{2}/\d{4}"))
                if date_tag:
                    date_text = date_tag.strip()

                # Skip irrelevant results
                keywords = ["fraud", "cyber", "upi", "digital payment",
                           "scam", "phishing", "arrest", "crime"]
                if not any(kw in title.lower() for kw in keywords):
                    continue

                results.append({
                    "title": title,
                    "date": date_text,
                    "url": link,
                    "source": "PIB",
                    "query": query,
                    "description": "",
                })

            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        logger.info(f"Found {len(results)} results for query '{query}'")
        return results

    def scrape_article(self, article: dict) -> dict:
        """Fetch full text of a single PIB article."""
        html = self.fetch(article["url"])
        if not html:
            return article

        soup = BeautifulSoup(html, "html.parser")

        # PIB article content is in div with id ContentPlaceHolder1_lblContent
        content_div = (
            soup.find("div", id="ContentPlaceHolder1_lblContent")
            or soup.find("div", class_="innner-page-content")
            or soup.find("div", id="PressReleaseContent")
        )

        if content_div:
            article["description"] = content_div.get_text(
                separator=" ", strip=True
            )
        else:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all("p")
            article["description"] = " ".join(
                p.get_text(strip=True) for p in paragraphs
            )

        return article

    def run(self, max_articles: int = 100) -> list[dict]:
        """
        Full scraping run across all search queries.
        Returns list of article dicts with full text.
        """
        all_articles = []
        seen_urls = set()

        for query in PIB_SEARCH_QUERIES:
            logger.info(f"Scraping PIB for query: '{query}'")
            articles = self.scrape_search_page(query)

            for article in articles:
                if article["url"] in seen_urls:
                    continue
                seen_urls.add(article["url"])

                # Fetch full article text
                article = self.scrape_article(article)
                all_articles.append(article)

                if len(all_articles) >= max_articles:
                    logger.info(f"Reached max_articles limit: {max_articles}")
                    break

            if len(all_articles) >= max_articles:
                break

        # Save combined output
        output_path = config.RAW_DIR / "pib_articles.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)

        logger.info(
            f"PIB scraping complete. "
            f"{len(all_articles)} articles saved to {output_path}"
        )
        return all_articles


if __name__ == "__main__":
    scraper = PIBScraper()
    articles = scraper.run(max_articles=50)
    print(f"\nCollected {len(articles)} articles")
    if articles:
        print("\nSample article:")
        print(f"  Title: {articles[0]['title']}")
        print(f"  Date:  {articles[0]['date']}")
        print(f"  URL:   {articles[0]['url']}")
        print(f"  Text preview: {articles[0]['description'][:200]}...")