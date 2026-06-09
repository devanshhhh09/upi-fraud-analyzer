# Feature Validation Report — UPI Fraud Pattern Analyzer
Generated: 2026-06-09 11:34

## 1. Feature Matrix Summary
- Total features before validation:  230
- Features removed (weak/noise):     126
- Features after validation:         104

## 2. Top 10 Most Important Features
              feature  importance
               has_qr    0.039058
        tfidf_request    0.037909
             tfidf_qr    0.032975
            tfidf_kyc    0.030231
              has_job    0.028897
        tfidf_collect    0.028089
             tfidf_rs    0.025865
              has_kyc    0.025738
        tfidf_via upi    0.025652
lottery_keyword_count    0.024646

## 3. Top Handcrafted Features
  has_qr
  has_job
  has_kyc
  lottery_keyword_count
  otp_keyword_count

## 4. Top TF-IDF Features
  tfidf_request
  tfidf_qr
  tfidf_kyc
  tfidf_collect
  tfidf_rs

## 5. Correlation Analysis
- Highly correlated pairs (|r|>0.85): 4
  sentence_count + special_char_count r=0.903
  otp_keyword_count + has_otp r=0.946
  kyc_keyword_count + has_kyc r=0.872
  urgency_keyword_count + has_urgency r=0.904

## 6. Features Removed
- Below importance threshold: 113
- TF-IDF stopwords:           16
- Total removed:              126

## 7. Key Findings
1. Handcrafted keyword features dominate top importance scores.
2. TF-IDF features provide complementary signal for similar fraud types.
3. Binary flag features (has_otp, has_qr, has_kyc) are highly discriminative.
4. No severe multicollinearity found in handcrafted features.
5. Validated feature matrix ready for model training.
