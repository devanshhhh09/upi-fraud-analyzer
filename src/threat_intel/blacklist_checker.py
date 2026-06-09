import json
import requests
import datetime
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

OPENPHISH_FEED = "https://openphish.com/feed.txt"
CACHE_PATH = config.RAW_DIR / "openphish_cache.txt"
CACHE_EXPIRY_HOURS = 6


def load_openphish_feed():
    if CACHE_PATH.exists():
        age_hours = (
            datetime.datetime.now() -
            datetime.datetime.fromtimestamp(CACHE_PATH.stat().st_mtime)
        ).seconds / 3600
        if age_hours < CACHE_EXPIRY_HOURS:
            logger.info("Using cached OpenPhish feed")
            return set(CACHE_PATH.read_text().splitlines())
    try:
        logger.info("Downloading OpenPhish feed...")
        response = requests.get(OPENPHISH_FEED, timeout=15)
        response.raise_for_status()
        urls = set(response.text.splitlines())
        CACHE_PATH.write_text(response.text)
        logger.info(f"OpenPhish feed: {len(urls)} URLs cached")
        return urls
    except Exception as e:
        logger.warning(f"OpenPhish feed download failed: {e}")
        if CACHE_PATH.exists():
            return set(CACHE_PATH.read_text().splitlines())
        return set()


def check_openphish(url):
    result = {'source': 'OpenPhish', 'found': False, 'error': None}
    try:
        feed = load_openphish_feed()
        result['found'] = url in feed
        logger.info(f"OpenPhish {url}: found={result['found']}")
    except Exception as e:
        result['error'] = str(e)[:100]
        logger.warning(f"OpenPhish check failed: {e}")
    return result


def check_blacklists(url):
    openphish_result = check_openphish(url)
    found_in_any     = openphish_result['found']
    sources_found    = ['OpenPhish'] if openphish_result['found'] else []
    status           = 'FOUND' if found_in_any else 'NOT FOUND'
    return {
        'url':       url,
        'status':    status,
        'found_in':  sources_found,
        'openphish': openphish_result,
    }


def format_blacklist_report(result):
    lines = [
        "── BLACKLIST STATUS ───────────────────────────────",
        f"URL:     {result['url']}",
        f"STATUS:  {result['status']}",
    ]
    if result['found_in']:
        lines.append(f"Found in: {', '.join(result['found_in'])}")
    lines.append("─" * 50)
    return "\n".join(lines)


if __name__ == "__main__":
    test_urls = [
        "https://www.google.com",
        "https://sbi-kyc-update.xyz",
    ]
    for url in test_urls:
        result = check_blacklists(url)
        print(format_blacklist_report(result))
        print()
