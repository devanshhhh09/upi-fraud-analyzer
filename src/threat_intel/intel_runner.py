from src.threat_intel.threat_intel import analyze_domain, format_report
from src.threat_intel.blacklist_checker import check_blacklists, format_blacklist_report
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


def full_intel_report(url):
    logger.info(f"Running full intel on: {url}")
    domain_analysis  = analyze_domain(url)
    blacklist_result = check_blacklists(url)
    combined = {**domain_analysis, 'blacklist': blacklist_result}
    return combined


def print_full_report(url):
    result = full_intel_report(url)
    print(format_report(result))
    print(format_blacklist_report(result['blacklist']))
    return result


if __name__ == "__main__":
    print("UPI FRAUD ANALYZER — THREAT INTELLIGENCE MODULE")
    print("=" * 55)
    test_urls = [
        "https://sbi-kyc-update.xyz",
        "https://hdfc-bank-reward.tk",
        "https://www.google.com",
    ]
    for url in test_urls:
        print(f"\n>>> Analyzing: {url}\n")
        print_full_report(url)
