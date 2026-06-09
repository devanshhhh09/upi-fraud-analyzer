import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix,
)
from xgboost import XGBClassifier
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


def load_labelled_features() -> tuple[pd.DataFrame, pd.Series, LabelEncoder]:
    """
    Load validated features, return only labelled records.
    Returns X, y, label_encoder.
    """
    df = pd.read_csv(
        config.FEATURES_DIR / 'features_validated.csv'
    )

    # Keep only labelled records for supervised training
    labelled = df[df['fraud_type'] != 'unlabelled'].copy()
    logger.info(f"Labelled records for training: {len(labelled)}")

    # Feature columns only
    feature_cols = [c for c in labelled.columns
                    if c not in ['fraud_type', 'source']]
    X = labelled[feature_cols].fillna(0)

    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(labelled['fraud_type'])

    logger.info(f"Classes: {list(le.classes_)}")
    logger.info(f"Feature matrix: {X.shape}")

    return X, y, le


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    le: LabelEncoder,
    model_name: str,
) -> dict:
    """Evaluate a trained model and return metrics dict."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    metrics = {
        'model':     model_name,
        'accuracy':  round(accuracy_score(y_test, y_pred), 4),
        'precision': round(precision_score(y_test, y_pred,
                           average='weighted', zero_division=0), 4),
        'recall':    round(recall_score(y_test, y_pred,
                           average='weighted', zero_division=0), 4),
        'f1':        round(f1_score(y_test, y_pred,
                           average='weighted', zero_division=0), 4),
        'roc_auc':   round(roc_auc_score(y_test, y_prob,
                           multi_class='ovr', average='weighted'), 4),
    }

    logger.info(f"\n{'='*50}")
    logger.info(f"Model: {model_name}")
    logger.info(f"Accuracy:  {metrics['accuracy']}")
    logger.info(f"Precision: {metrics['precision']}")
    logger.info(f"Recall:    {metrics['recall']}")
    logger.info(f"F1 Score:  {metrics['f1']}")
    logger.info(f"ROC-AUC:   {metrics['roc_auc']}")
    logger.info(f"\nClassification Report:\n"
                f"{classification_report(y_test, y_pred, target_names=le.classes_)}")

    return metrics


def train_all_models() -> dict:
    """
    Train Logistic Regression, Random Forest, and XGBoost.
    Evaluate each and return results.
    """
    X, y, le = load_labelled_features()

    # Train/test split — stratified to keep class balance
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=config.RANDOM_STATE,
        stratify=y,
    )

    logger.info(f"Train size: {len(X_train)} | Test size: {len(X_test)}")

    cv = StratifiedKFold(n_splits=5, shuffle=True,
                         random_state=config.RANDOM_STATE)

    results = {}

    # ── 1. Logistic Regression ────────────────────────────────────────
    logger.info("\nTraining Logistic Regression...")
    lr = LogisticRegression(
        max_iter=1000,
        random_state=config.RANDOM_STATE,
        C=1.0,
        solver='lbfgs',
        multi_class='multinomial',
    )
    lr.fit(X_train, y_train)

    cv_scores = cross_val_score(lr, X, y, cv=cv,
                                scoring='f1_weighted')
    logger.info(f"LR CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    metrics_lr = evaluate_model(lr, X_test, y_test, le, 'Logistic Regression')
    metrics_lr['cv_f1_mean'] = round(cv_scores.mean(), 4)
    metrics_lr['cv_f1_std']  = round(cv_scores.std(), 4)
    results['logistic_regression'] = metrics_lr

    joblib.dump(lr, config.MODELS_DIR / 'logistic_regression.pkl')
    logger.info("Logistic Regression saved.")

    # ── 2. Random Forest ─────────────────────────────────────────────
    logger.info("\nTraining Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    cv_scores = cross_val_score(rf, X, y, cv=cv,
                                scoring='f1_weighted')
    logger.info(f"RF CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    metrics_rf = evaluate_model(rf, X_test, y_test, le, 'Random Forest')
    metrics_rf['cv_f1_mean'] = round(cv_scores.mean(), 4)
    metrics_rf['cv_f1_std']  = round(cv_scores.std(), 4)
    results['random_forest'] = metrics_rf

    joblib.dump(rf, config.MODELS_DIR / 'random_forest.pkl')
    logger.info("Random Forest saved.")

    # ── 3. XGBoost ───────────────────────────────────────────────────
    logger.info("\nTraining XGBoost...")
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=config.RANDOM_STATE,
        eval_metric='mlogloss',
        verbosity=0,
        use_label_encoder=False,
    )
    xgb.fit(X_train, y_train)

    cv_scores = cross_val_score(xgb, X, y, cv=cv,
                                scoring='f1_weighted')
    logger.info(f"XGB CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    metrics_xgb = evaluate_model(xgb, X_test, y_test, le, 'XGBoost')
    metrics_xgb['cv_f1_mean'] = round(cv_scores.mean(), 4)
    metrics_xgb['cv_f1_std']  = round(cv_scores.std(), 4)
    results['xgboost'] = metrics_xgb

    joblib.dump(xgb, config.MODELS_DIR / 'xgboost.pkl')
    logger.info("XGBoost saved.")

    # Save label encoder
    joblib.dump(le, config.MODELS_DIR / 'label_encoder.pkl')

    return results, X_test, y_test, le


if __name__ == "__main__":
    results, X_test, y_test, le = train_all_models()

    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    print(f"{'Model':<25} {'Accuracy':>10} {'Precision':>10} "
          f"{'Recall':>8} {'F1':>8} {'ROC-AUC':>10}")
    print("-"*60)
    for name, m in results.items():
        print(f"{m['model']:<25} {m['accuracy']:>10} {m['precision']:>10} "
              f"{m['recall']:>8} {m['f1']:>8} {m['roc_auc']:>10}")
    print("="*60)

    best = max(results.values(), key=lambda x: x['precision'])
    print(f"\nBest model by precision: {best['model']} ({best['precision']})")
