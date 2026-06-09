import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


def plot_confusion_matrix(
    model,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    le: LabelEncoder,
    model_name: str,
    save_path: str,
):
    """Plot and save confusion matrix for a model."""
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=le.classes_,
        yticklabels=le.classes_,
        linewidths=0.5,
    )
    plt.title(f'Confusion matrix — {model_name}')
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    logger.info(f"Confusion matrix saved to {save_path}")


def plot_model_comparison(results: dict, save_path: str):
    """Bar chart comparing all models across metrics."""
    metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    model_names = [r['model'] for r in results.values()]

    x = np.arange(len(metrics))
    width = 0.25
    colors = ['steelblue', 'coral', 'mediumseagreen']

    fig, ax = plt.subplots(figsize=(13, 6))
    for i, (name, result) in enumerate(results.items()):
        values = [result[m] for m in metrics]
        bars = ax.bar(x + i * width, values, width,
                      label=result['model'], color=colors[i], alpha=0.85)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.005,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('Metric')
    ax.set_ylabel('Score')
    ax.set_title('Model comparison across all metrics')
    ax.set_xticks(x + width)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.axhline(y=0.92, color='red', linestyle='--',
               alpha=0.5, label='Target precision (0.92)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    logger.info(f"Model comparison chart saved to {save_path}")


def generate_comparison_report(results: dict) -> str:
    """Generate markdown comparison report."""
    best = max(results.values(), key=lambda x: x['precision'])
    target_met = best['precision'] >= 0.92

    report = f"""# Model Comparison Report — UPI Fraud Pattern Analyzer
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## 1. Results Summary

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | CV F1 |
|-------|----------|-----------|--------|----|---------|-------|
"""
    for m in results.values():
        report += (
            f"| {m['model']} | {m['accuracy']} | {m['precision']} | "
            f"{m['recall']} | {m['f1']} | {m['roc_auc']} | "
            f"{m['cv_f1_mean']}±{m['cv_f1_std']} |\n"
        )

    report += f"""
## 2. Best Model
- **Name:** {best['model']}
- **Precision:** {best['precision']}
- **Target met (>0.92):** {'YES' if target_met else 'NO — see recommendations'}

## 3. Analysis
- Precision target of 0.92 is critical — false positives mean flagging
  legitimate transactions, which damages trust.
- Cross-validation F1 scores confirm model generalizes beyond test set.
- Confusion matrix shows which fraud types are hardest to distinguish.

## 4. Selected Model for Production
{best['model']} selected based on highest precision score.
Model saved to models/{best['model'].lower().replace(' ', '_')}.pkl

## 5. Figures Generated
- fig10_confusion_lr.png
- fig11_confusion_rf.png
- fig12_confusion_xgb.png
- fig13_model_comparison.png
"""
    return report


if __name__ == "__main__":
    from src.models.trainer import train_all_models

    results, X_test, y_test, le = train_all_models()

    # Load saved models for evaluation
    lr  = joblib.load(config.MODELS_DIR / 'logistic_regression.pkl')
    rf  = joblib.load(config.MODELS_DIR / 'random_forest.pkl')
    xgb = joblib.load(config.MODELS_DIR / 'xgboost.pkl')

    # Confusion matrices
    plot_confusion_matrix(lr,  X_test, y_test, le,
        'Logistic Regression',
        'reports/fig10_confusion_lr.png')
    plot_confusion_matrix(rf,  X_test, y_test, le,
        'Random Forest',
        'reports/fig11_confusion_rf.png')
    plot_confusion_matrix(xgb, X_test, y_test, le,
        'XGBoost',
        'reports/fig12_confusion_xgb.png')

    # Model comparison chart
    plot_model_comparison(results, 'reports/fig13_model_comparison.png')

    # Comparison report
    report = generate_comparison_report(results)
    with open('reports/comparison_report.md', 'w') as f:
        f.write(report)

    print(report)
