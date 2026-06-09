import sys
sys.path.insert(0, '/Users/devansh/Desktop/upi-fraud-analyzer')

import pytest
import pandas as pd
from src.features.feature_extractor import extract_features, keyword_count, extract_amount


class TestKeywordCount:
    def test_counts_present_keywords(self):
        text = "I shared my OTP and lost money via UPI"
        assert keyword_count(text, ['otp', 'upi']) == 2

    def test_returns_zero_for_no_match(self):
        assert keyword_count("hello world", ['otp', 'kyc']) == 0

    def test_case_insensitive(self):
        assert keyword_count("OTP FRAUD", ['otp']) == 1

    def test_empty_text(self):
        assert keyword_count("", ['otp']) == 0


class TestExtractAmount:
    def test_extracts_rs_amount(self):
        assert extract_amount("I lost Rs 15000 in fraud") == 15000.0

    def test_extracts_rupee_symbol(self):
        assert extract_amount("Payment of ₹5000 was deducted") == 5000.0

    def test_extracts_comma_amount(self):
        assert extract_amount("Lost Rs 1,50,000 total") == 150000.0

    def test_returns_zero_for_no_amount(self):
        assert extract_amount("No amount mentioned here") == 0.0

    def test_ignores_small_amounts(self):
        # Amounts below 100 are filtered
        assert extract_amount("Paid Rs 50 only") == 0.0

    def test_returns_max_amount(self):
        result = extract_amount("First Rs 5000 then Rs 20000 total")
        assert result == 20000.0


class TestExtractFeatures:
    def test_returns_dict(self):
        result = extract_features("UPI fraud complaint text")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = extract_features("test text")
        required = [
            'text_length', 'word_count', 'has_otp',
            'has_qr', 'has_kyc', 'has_collect',
            'upi_keyword_count', 'amount_value',
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_detects_otp(self):
        result = extract_features("Please share the OTP")
        assert result['has_otp'] == 1

    def test_detects_qr(self):
        result = extract_features("Scan the QR code to pay")
        assert result['has_qr'] == 1

    def test_detects_kyc(self):
        result = extract_features("Your KYC is pending")
        assert result['has_kyc'] == 1

    def test_detects_amount(self):
        result = extract_features("Lost Rs 25000 in fraud")
        assert result['has_amount'] == 1
        assert result['amount_value'] == 25000.0

    def test_text_length(self):
        text   = "Hello world"
        result = extract_features(text)
        assert result['text_length'] == len(text)

    def test_empty_text(self):
        result = extract_features("")
        assert result['text_length'] == 0
        assert result['word_count']  == 0

    def test_detects_investment_keywords(self):
        result = extract_features("Join our Telegram group for trading profits")
        assert result['has_telegram']   == 1
        assert result['has_investment'] == 1
