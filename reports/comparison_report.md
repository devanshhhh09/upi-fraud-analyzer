# Model Comparison Report — UPI Fraud Pattern Analyzer
Generated: 2026-06-09 11:47

## 1. Results Summary

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV F1 |
|-------|----------|-----------|--------|----|---------|-------|
| Logistic Regression | 0.5625 | 0.5625 | 0.5625 | 0.525 | 0.8616 | 0.4846±0.0836 |
| Random Forest | 0.875 | 0.9375 | 0.875 | 0.875 | 0.9978 | 0.9142±0.0722 |
| XGBoost | 0.875 | 0.9375 | 0.875 | 0.875 | 0.9955 | 0.8683±0.0409 |

## 2. Best Model
- **Name:** Random Forest
- **Precision:** 0.9375
- **Target met (>0.92):** YES

## 3. Analysis
- Precision target of 0.92 is critical — false positives mean flagging
  legitimate transactions, which damages trust.
- Cross-validation F1 scores confirm model generalizes beyond test set.
- Confusion matrix shows which fraud types are hardest to distinguish.

## 4. Selected Model for Production
Random Forest selected based on highest precision score.
Model saved to models/random_forest.pkl

## 5. Figures Generated
- fig10_confusion_lr.png
- fig11_confusion_rf.png
- fig12_confusion_xgb.png
- fig13_model_comparison.png
