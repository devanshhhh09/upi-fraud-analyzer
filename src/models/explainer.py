import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


class FraudExplainer:
    """
    Explains Random Forest predictions using SHAP values.
    Provides both visual and text explanations for investigators.
    """

    def __init__(self):
        self.model     = joblib.load(config.MODELS_DIR / 'random_forest.pkl')
        self.le        = joblib.load(config.MODELS_DIR / 'label_encoder.pkl')
        self.explainer = None
        self.feature_cols = None
        logger.info("FraudExplainer loaded model and label encoder")

    def fit(self, X_train: pd.DataFrame):
        """Fit SHAP TreeExplainer on training data."""
        logger.info("Fitting SHAP TreeExplainer...")
        self.feature_cols = list(X_train.columns)
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP explainer ready")

    def explain_prediction(
        self,
        X_single: pd.DataFrame,
        top_n: int = 5,
    ) -> dict:
        """
        Explain a single prediction in plain text.

        Returns dict with:
            prediction, confidence, fraud_type_label,
            top_reasons (list of dicts)
        """
        if self.explainer is None:
            raise RuntimeError("Call fit() before explain_prediction()")

        # Get prediction and confidence
        pred_encoded = self.model.predict(X_single)[0]
        pred_proba   = self.model.predict_proba(X_single)[0]
        confidence   = round(float(pred_proba[pred_encoded]) * 100, 1)
        fraud_label  = self.le.inverse_transform([pred_encoded])[0]

        # Get SHAP values for this prediction
        shap_values  = self.explainer.shap_values(X_single)

        # shap_values shape: [n_classes, n_samples, n_features]
        # Get SHAP values for the predicted class
        class_shap = shap_values[0] if isinstance(shap_values, list) == False else shap_values[pred_encoded][0]

        # Build feature contribution list
        feature_contributions = []
        class_shap_flat = np.array(class_shap).flatten()
        for i, feat in enumerate(self.feature_cols):
            if i >= len(class_shap_flat):
                break
            shap_val = float(class_shap_flat[i])
            feat_value = float(X_single.iloc[0, i])
            if abs(shap_val) > 0.001:
                feature_contributions.append({
                    'feature':    feat,
                    'value':      feat_value,
                    'shap_value': round(shap_val, 4),
                    'direction':  'toward' if shap_val > 0 else 'away',
                })

        # Sort by absolute SHAP value
        feature_contributions.sort(
            key=lambda x: abs(x['shap_value']), reverse=True
        )
        top_reasons = feature_contributions[:top_n]

        return {
            'prediction':       fraud_label,
            'confidence':       confidence,
            'all_probabilities': {
                self.le.inverse_transform([i])[0]: round(float(p) * 100, 1)
                for i, p in enumerate(pred_proba)
            },
            'top_reasons': top_reasons,
        }

    def format_explanation(self, explanation: dict) -> str:
        """Format explanation as human-readable text for investigators."""
        lines = [
            f"PREDICTION:  {explanation['prediction'].upper().replace('_', ' ')}",
            f"CONFIDENCE:  {explanation['confidence']}%",
            "",
            "TOP REASONS:",
        ]

        for r in explanation['top_reasons']:
            direction = "+" if r['direction'] == 'toward' else "-"
            feat_name = r['feature'].replace('_', ' ').replace('tfidf ', '')
            lines.append(
                f"  {direction} {feat_name:<35} "
                f"value={r['value']:.0f}  "
                f"impact={r['shap_value']:+.4f}"
            )

        lines += [
            "",
            "PROBABILITY BREAKDOWN:",
        ]
        for fraud_type, prob in sorted(
            explanation['all_probabilities'].items(),
            key=lambda x: x[1], reverse=True
        ):
            bar = '█' * int(prob / 5)
            lines.append(f"  {fraud_type:<25} {prob:>5.1f}%  {bar}")

        return "\n".join(lines)

    def plot_shap_summary(
        self,
        X: pd.DataFrame,
        save_path: str = 'reports/fig14_shap_summary.png',
    ):
        """Plot SHAP summary for all predictions."""
        logger.info("Generating SHAP summary plot...")
        shap_values = self.explainer.shap_values(X)

        # Use mean absolute SHAP across all classes
        if isinstance(shap_values, list):
            mean_shap = np.mean(np.abs(np.array(shap_values)), axis=0)
        else:
            mean_shap = np.mean(np.abs(shap_values), axis=2).mean(axis=0, keepdims=True)

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            mean_shap,
            X,
            feature_names=self.feature_cols,
            plot_type='bar',
            max_display=20,
            show=False,
        )
        plt.title('Top 20 features by mean SHAP importance')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"SHAP summary saved to {save_path}")

    def plot_shap_single(
        self,
        X_single: pd.DataFrame,
        save_path: str = 'reports/fig15_shap_single.png',
    ):
        """Plot SHAP waterfall for a single prediction."""
        logger.info("Generating SHAP single prediction plot...")
        shap_values = self.explainer.shap_values(X_single)

        pred_encoded = self.model.predict(X_single)[0]
        if isinstance(shap_values, list):
            class_shap = shap_values[pred_encoded][0]
        else:
            class_shap = shap_values[0, :, pred_encoded]
        class_shap = np.array(class_shap).flatten()
        if isinstance(self.explainer.expected_value, (list, np.ndarray)):
            base_value = float(self.explainer.expected_value[pred_encoded])
        else:
            base_value = float(self.explainer.expected_value)

        explanation = shap.Explanation(
            values=class_shap,
            base_values=base_value,
            data=X_single.iloc[0].values,
            feature_names=self.feature_cols,
        )

        plt.figure(figsize=(12, 6))
        shap.plots.waterfall(explanation, max_display=15, show=False)
        plt.title('SHAP waterfall — single prediction explanation')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"SHAP waterfall saved to {save_path}")


if __name__ == "__main__":
    from src.models.trainer import load_labelled_features
    from sklearn.model_selection import train_test_split

    # Load data
    X, y, le = load_labelled_features()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=config.RANDOM_STATE,
        stratify=y,
    )

    # Fit explainer
    explainer = FraudExplainer()
    explainer.fit(X_train)

    # --- Test 1: Explain a single prediction ---
    print("\n" + "="*60)
    print("SINGLE PREDICTION EXPLANATION")
    print("="*60)

    sample = X_test.iloc[[0]]
    true_label = le.inverse_transform([y_test[0]])[0]
    print(f"True label: {true_label}")

    explanation = explainer.explain_prediction(sample)
    print(explainer.format_explanation(explanation))

    # --- Test 2: Explain all test records ---
    print("\n" + "="*60)
    print("ALL TEST PREDICTIONS WITH EXPLANATIONS")
    print("="*60)

    correct = 0
    for i in range(len(X_test)):
        sample     = X_test.iloc[[i]]
        true_label = le.inverse_transform([y_test[i]])[0]
        exp        = explainer.explain_prediction(sample, top_n=3)

        status = "✓" if exp['prediction'] == true_label else "✗"
        print(f"\n{status} Record {i+1}")
        print(f"  True:      {true_label}")
        print(f"  Predicted: {exp['prediction']} ({exp['confidence']}%)")
        print(f"  Top reason: {exp['top_reasons'][0]['feature']} "
              f"= {exp['top_reasons'][0]['value']:.0f}" if exp['top_reasons'] else "")

        if exp['prediction'] == true_label:
            correct += 1

    print(f"\nExplained predictions correct: {correct}/{len(X_test)}")

    # --- Generate SHAP plots ---
    print("\nGenerating SHAP visualizations...")
    explainer.plot_shap_summary(X_test)
    explainer.plot_shap_single(X_test.iloc[[0]])

    print("\nPhase 7 complete.")
    print("Figures saved:")
    print("  reports/fig14_shap_summary.png")
    print("  reports/fig15_shap_single.png")
