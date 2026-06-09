import re
import pandas as pd
import numpy as np
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


# ── Indian fraud keyword lists ────────────────────────────────────────

UPI_KEYWORDS = [
    'upi', 'gpay', 'phonepe', 'paytm', 'bhim', 'npci',
    'vpa', 'collect', 'request', 'qr', 'scan',
]

OTP_KEYWORDS = [
    'otp', 'one time password', 'verification code',
    'share otp', 'enter otp', 'sms code',
]

KYC_KEYWORDS = [
    'kyc', 'know your customer', 'aadhaar', 'aadhar',
    'pan card', 'verify account', 'account freeze',
    'account block', 'account suspend',
]

BANK_KEYWORDS = [
    'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb',
    'bank account', 'net banking', 'debit card',
    'credit card', 'ifsc', 'account number',
]

INVESTMENT_KEYWORDS = [
    'invest', 'return', 'profit', 'trading', 'crypto',
    'bitcoin', 'telegram group', 'stock tip', 'guaranteed return',
    'double money', 'passive income', 'forex',
]

JOB_KEYWORDS = [
    'job offer', 'work from home', 'salary', 'hiring',
    'placement', 'registration fee', 'security deposit',
    'offer letter', 'joining fee', 'training fee',
]

LOTTERY_KEYWORDS = [
    'prize', 'winner', 'lucky draw', 'lottery', 'reward',
    'congratulations', 'selected', 'claim prize',
    'processing fee', 'tax payment',
]

URGENCY_KEYWORDS = [
    'immediately', 'urgent', 'expire', 'block', 'suspend',
    'within 24 hours', 'act now', 'last chance',
    'permanent block', 'immediately', 'right now',
]

AMOUNT_PATTERN = re.compile(
    r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)|'
    r'₹\s*(\d+(?:,\d+)*)|'
    r'(\d+(?:,\d+)*)\s*(?:rupees|rs)',
    re.IGNORECASE
)


def keyword_count(text: str, keywords: list) -> int:
    """Count how many keywords appear in the text."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def extract_amount(text: str) -> float:
    """Extract maximum rupee amount from text."""
    amounts = []
    for match in AMOUNT_PATTERN.finditer(str(text)):
        for group in match.groups():
            if group:
                try:
                    amount = float(group.replace(',', ''))
                    if 100 <= amount <= 10_000_000:
                        amounts.append(amount)
                except ValueError:
                    continue
    return max(amounts) if amounts else 0.0


def extract_features(text: str, title: str = '') -> dict:
    """
    Extract all features from a single complaint text.
    Returns a dictionary of feature name -> value.
    """
    full_text = f"{title} {text}".strip()
    text_lower = full_text.lower()

    # ── Basic text features ───────────────────────────────────────────
    features = {
        'text_length':     len(full_text),
        'word_count':      len(full_text.split()),
        'sentence_count':  len(re.split(r'[.!?]+', full_text)),
        'avg_word_length': np.mean([len(w) for w in full_text.split()])
                           if full_text.split() else 0,
        'digit_count':     sum(c.isdigit() for c in full_text),
        'upper_count':     sum(c.isupper() for c in full_text),
        'special_char_count': sum(not c.isalnum() and not c.isspace()
                                  for c in full_text),
    }

    # ── Keyword group features ────────────────────────────────────────
    features.update({
        'upi_keyword_count':        keyword_count(text_lower, UPI_KEYWORDS),
        'otp_keyword_count':        keyword_count(text_lower, OTP_KEYWORDS),
        'kyc_keyword_count':        keyword_count(text_lower, KYC_KEYWORDS),
        'bank_keyword_count':       keyword_count(text_lower, BANK_KEYWORDS),
        'investment_keyword_count': keyword_count(text_lower, INVESTMENT_KEYWORDS),
        'job_keyword_count':        keyword_count(text_lower, JOB_KEYWORDS),
        'lottery_keyword_count':    keyword_count(text_lower, LOTTERY_KEYWORDS),
        'urgency_keyword_count':    keyword_count(text_lower, URGENCY_KEYWORDS),
    })

    # ── Specific signal features ──────────────────────────────────────
    features.update({
        'has_otp':          int('otp' in text_lower),
        'has_qr':           int('qr' in text_lower or 'qr code' in text_lower),
        'has_kyc':          int('kyc' in text_lower),
        'has_collect':      int('collect' in text_lower),
        'has_aadhaar':      int('aadhaar' in text_lower or 'aadhar' in text_lower),
        'has_telegram':     int('telegram' in text_lower),
        'has_whatsapp':     int('whatsapp' in text_lower),
        'has_lottery':      int('lottery' in text_lower or 'prize' in text_lower),
        'has_job':          int('job' in text_lower or 'salary' in text_lower),
        'has_investment':   int('invest' in text_lower or 'trading' in text_lower),
        'has_urgency':      int(any(w in text_lower for w in
                                ['urgent', 'immediately', 'expire', 'block'])),
        'has_amount':       int(extract_amount(full_text) > 0),
        'amount_value':     extract_amount(full_text),
        'has_bank_name':    int(any(b in text_lower for b in
                                ['sbi', 'hdfc', 'icici', 'axis', 'kotak'])),
        'has_upi_app':      int(any(a in text_lower for a in
                                ['phonepe', 'gpay', 'paytm', 'bhim'])),
    })

    return features


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature extraction to every row in the dataframe.
    Returns a dataframe of features with fraud_type label.
    """
    logger.info(f"Extracting features from {len(df)} records...")

    feature_rows = []
    for idx, row in df.iterrows():
        text  = str(row.get('text', ''))
        title = str(row.get('title', ''))
        feats = extract_features(text, title)
        feats['fraud_type'] = row.get('fraud_type', 'unlabelled')
        feats['source']     = row.get('source', '')
        feature_rows.append(feats)

    features_df = pd.DataFrame(feature_rows)
    logger.info(f"Feature matrix shape: {features_df.shape}")
    return features_df


if __name__ == "__main__":
    # Load cleaned dataset
    df = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
    logger.info(f"Loaded {len(df)} records")

    # Build feature matrix
    features_df = build_feature_matrix(df)

    # Save
    output_path = config.FEATURES_DIR / 'features.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)

    logger.info(f"Features saved to {output_path}")

    # Summary
    print(f"\nFeature matrix shape: {features_df.shape}")
    print(f"\nFeature columns ({len(features_df.columns)} total):")
    for col in features_df.columns:
        print(f"  {col}")
    print(f"\nSample row (first record):")
    print(features_df.iloc[0].to_string())
