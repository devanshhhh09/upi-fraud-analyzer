# paste the entire base_scraper.py code here
import time
import random
import requests
from pathlib import Path
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseScraper:
    """
    Base class for all scrapers in the UPI Fraud Analyzer.

    Handles:
    - Polite rate limiting (random delay between requests)
    - Automatic retries on failure
    - Raw HTML saving for reproducibility
    - Consistent headers to avoid bot detection
    """

    BASE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(
        self,
        output_dir: Path,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        max_retries: int = 3,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(self.BASE_HEADERS)

    def fetch(self, url: str) -> Optional[str]:
        """
        Fetch a URL with retries and polite delay.
        Returns HTML string or None on failure.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Fetching [{attempt}/{self.max_retries}]: {url}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                self._polite_delay()
                return response.text

            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error {e.response.status_code} for {url}")
                if e.response.status_code == 429:
                    # Rate limited — wait longer
                    logger.warning("Rate limited. Waiting 30 seconds...")
                    time.sleep(30)
                elif e.response.status_code in (403, 404):
                    # Not recoverable
                    logger.error(f"Unrecoverable HTTP error for {url}")
                    return None

            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt} for {url}")
                time.sleep(5)

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt} for {url}")
                time.sleep(5)

        logger.error(f"All {self.max_retries} attempts failed for {url}")
        return None

    def save_raw(self, filename: str, content: str) -> Path:
        """Save raw HTML to disk for reproducibility."""
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.info(f"Saved raw file: {path}")
        return path

    def _polite_delay(self):
        """Wait a random amount of time between requests."""
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.info(f"Waiting {delay:.1f}s before next request...")
        time.sleep(delay)