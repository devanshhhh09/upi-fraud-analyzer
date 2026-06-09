# Manual Test Cases — UPI Fraud Analyzer

## Category 1: Legitimate URLs (expected: LOW risk)

| URL | Expected Risk | Expected Score |
|-----|--------------|----------------|
| https://www.google.com | LOW | < 25 |
| https://www.sbi.co.in | LOW | < 25 |
| https://www.rbi.org.in | LOW | < 25 |
| https://www.npci.org.in | LOW | < 25 |

## Category 2: Known Fraud Patterns (expected: HIGH/CRITICAL)

| URL | Expected Risk | Key Indicators |
|-----|--------------|----------------|
| https://sbi-kyc-update.xyz | CRITICAL | SBI impersonation, .xyz TLD |
| https://hdfc-bank-verify.tk | CRITICAL | HDFC impersonation, .tk TLD |
| https://paytm-reward-claim.online | CRITICAL | Paytm impersonation, .online TLD |
| https://uidai-aadhaar-update.ml | CRITICAL | UIDAI impersonation, .ml TLD |

## Category 3: Complaint Classification

| Complaint Text | Expected Type | Key Features |
|----------------|--------------|--------------|
| "Received OTP request from fake SBI" | otp_relay | has_otp=1 |
| "Scanned QR code, money gone" | qr_swap | has_qr=1 |
| "KYC freeze message, entered Aadhaar" | fake_kyc_freeze | has_kyc=1, has_aadhaar=1 |
| "Collect request from unknown UPI" | fake_collect_request | has_collect=1 |
| "Telegram group promised 30% returns" | investment_scam | has_telegram=1 |
| "Job offer asked for security deposit" | job_advance_fee | has_job=1 |
| "Won KBC lottery, pay tax first" | lottery_reward | has_lottery=1 |
| "Paid fake merchant on OLX, no delivery" | fake_merchant | keyword: product |

## Category 4: Edge Cases

| Input | Expected Behaviour |
|-------|-------------------|
| Empty text | 400 Bad Request |
| Text under 10 chars | 400 Bad Request |
| Text in Hindi | Prediction returned (may have lower confidence) |
| Very long text (5000+ chars) | Prediction returned without crash |
| URL without http:// | Domain extracted correctly |
| IP address as URL | Processed without crash |
| Special characters in text | Processed without crash |

## Category 5: API Edge Cases

| Request | Expected |
|---------|----------|
| POST /api/predict with no body | 400 |
| POST /api/predict with missing 'text' | 400 |
| GET /api/search with no query | 400 |
| GET /api/search?q=xyz&limit=0 | Empty results |
| POST /api/intel with invalid URL | Processed with partial data |
