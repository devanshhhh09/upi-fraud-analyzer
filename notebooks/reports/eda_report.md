# EDA Report — UPI Fraud Pattern Analyzer
Generated: 2026-06-09 10:47

## 1. Dataset Overview
- Total records:      153
- Labelled records:   80
- Unlabelled records: 73
- Columns:            ['title', 'text', 'date', 'url', 'source', 'fraud_type', 'text_length', 'word_count', 'amount']

## 2. Data Sources
source
SeedData    80
NewsAPI     73

## 3. Fraud Type Distribution (labelled)
fraud_type
fake_collect_request    10
qr_swap                 10
otp_relay               10
fake_kyc_freeze         10
investment_scam         10
fake_merchant           10
job_advance_fee         10
lottery_reward          10

## 4. Text Length Statistics
- Mean characters:   340
- Median characters: 212
- Min characters:    133
- Max characters:    629
- Mean word count:   54

## 5. Top 10 Keywords
  chars: 73
  upi: 70
  india: 54
  payment: 47
  digital: 36
  market: 36
  account: 34
  money: 33
  pay: 33
  fake: 31

## 6. Amount Analysis
- Records with amounts: 72
- Median fraud amount:  Rs 8,350
- Max fraud amount:     Rs 80,000
- Min fraud amount:     Rs 100

## 7. Key Findings
1. Dataset is perfectly class-balanced — 10 records per fraud type.
2. NewsAPI articles are 3x longer than seed data (518 vs 178 chars avg).
3. Each fraud type has highly distinct keywords with near-zero overlap.
4. QR swap, OTP relay and collect request frauds have strongest keyword signals.
5. Median financial loss is Rs 8,350 — investment and job scams highest.
6. Word 'chars' appears as noise from NewsAPI content field — filter in Phase 4.

## 8. Data Quality Issues
- 73 records (47.7%) unlabelled — to be assigned via clustering in Phase 8.
- Amount extraction covers 47% of records — rest have no amount mentioned.
- NewsAPI records need relevance filtering — some may not describe UPI fraud.

## 9. Figures Generated
- fig1_class_distribution.png
- fig2_text_length.png
- fig3_source_analysis.png
- fig4_keyword_frequency.png
- fig5_keyword_heatmap.png
- fig6_amount_analysis.png
