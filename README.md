# UPI Fraud Pattern Analyzer

> AI-powered fraud detection and threat intelligence system for UPI complaints — built for Gurugram Police GPCSSI 2026

## Live Demo

**Dashboard:** https://upi-fraud-analyzer.onrender.com

**API Health:** https://upi-fraud-analyzer.onrender.com/api/health

> Note: Free tier spins down after inactivity. First load may take 30-60 seconds.

---

## Project Overview

UPI fraud is Indias fastest growing cyber crime. This system classifies UPI fraud complaints by modus operandi and provides actionable threat intelligence to investigators.

Built as a GPCSSI 2026 internship project for Gurugram Police Cyber Cell.

---

## Fraud Typologies Detected

- fake_collect_request: Fraudster sends UPI collect request disguised as payment
- qr_swap: QR code replaced with fraudsters code at merchant location
- otp_relay: Victim tricked into sharing OTP
- fake_kyc_freeze: Account freeze threat to extract credentials
- investment_scam: Fake returns promised via UPI payments
- fake_merchant: Non-existent seller collects payment
- job_advance_fee: Fake job offer collects registration deposit
- lottery_reward: Prize claim requires advance fee payment

---

## Model Performance

| Model | Precision | Recall | F1 | ROC-AUC |
|-------|-----------|--------|----|---------|
| Logistic Regression | 0.56 | 0.56 | 0.52 | 0.88 |
| Random Forest | 0.96 | 0.94 | 0.93 | 0.99 |
| XGBoost | 0.94 | 0.88 | 0.88 | 0.99 |

Selected model: Random Forest with precision 0.96 and CV F1 0.91

---

## Quick Start

Clone the repository and run locally:

    git clone https://github.com/devanshhhh09/upi-fraud-analyzer.git
    cd upi-fraud-analyzer
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    bash build.sh
    python app.py

Open http://localhost:5001 in your browser.

Or use Docker:

    docker-compose up

---

## API Reference

Base URL: https://upi-fraud-analyzer.onrender.com

- POST /api/predict — Classify a fraud complaint
- POST /api/intel  — Analyze a suspicious URL
- GET  /api/trends — Fraud type distribution
- GET  /api/search?q=keyword — Search complaints
- GET  /api/history — All previous scans
- GET  /api/health  — Service health check

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, Flask 3.1 |
| ML Models | scikit-learn, XGBoost |
| Explainability | SHAP |
| Database | SQLite + Flask-SQLAlchemy |
| Frontend | Bootstrap 5, Chart.js |
| Deployment | Render, Docker |
| Testing | pytest (39 tests passing) |

---

## Project Structure

    upi-fraud-analyzer/
    src/ingestion/       Data scrapers
    src/features/        Feature extraction
    src/models/          ML training and SHAP
    src/threat_intel/    WHOIS DNS blacklist
    src/api/             Flask routes and database
    templates/           Web dashboard pages
    tests/               39 automated tests
    app.py               Flask entry point
    Dockerfile           Docker container
    build.sh             Deployment build script

---

## GPCSSI 2026

- Track: Technical Projects — Cyber Security
- Category: AI/ML for Cyber Crime Detection
- Student: Devansh — B.Tech Computer Science, 3rd Year
- Institution: Dr Shakuntala Mishra National Rehabilitation University, Lucknow

---

## Author

Devansh
B.Tech Computer Science, 3rd Year
Dr Shakuntala Mishra National Rehabilitation University, Lucknow
GPCSSI 2026 Intern — Gurugram Police
GitHub: https://github.com/devanshhhh09
