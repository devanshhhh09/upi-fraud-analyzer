import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
BRIEFS_DIR = REPORTS_DIR / "briefs"

# API keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Model settings
RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_CLUSTER_SIZE = 5

# Fraud taxonomy labels
FRAUD_TYPES = [
    "fake_collect_request",
    "qr_swap",
    "otp_relay",
    "fake_kyc_freeze",
    "investment_scam",
    "fake_merchant",
    "job_advance_fee",
    "lottery_reward",
    "unknown",
]

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi", "unknown"]
