import pandas as pd
import numpy as np
from src.features.feature_extractor import build_feature_matrix
from src.features.tfidf_vectorizer import build_tfidf_features
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


def build_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build complete feature matrix combining:
    1. Handcrafted features (keyword counts, flags, amounts)
    2. TF-IDF text features

    Returns combined DataFrame ready for ML training.
    """
    logger.info("Building handcrafted features...")
    handcrafted_df = build_feature_matrix(df)

    logger.info("Building TF-IDF features...")
    tfidf_df, _ = build_tfidf_features(df, max_features=200)

    # Separate labels before combining
    labels = handcrafted_df[['fraud_type', 'source']].reset_index(drop=True)
    handcrafted_features = handcrafted_df.drop(
        columns=['fraud_type', 'source']
    ).reset_index(drop=True)
    tfidf_features = tfidf_df.reset_index(drop=True)

    # Combine all features
    combined = pd.concat(
        [handcrafted_features, tfidf_features, labels],
        axis=1
    )

    logger.info(f"Combined feature matrix: {combined.shape}")
    return combined


if __name__ == "__main__":
    # Load data
    df = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
    logger.info(f"Loaded {len(df)} records")

    # Build all features
    combined = build_all_features(df)

    # Save
    output_path = config.FEATURES_DIR / 'features_combined.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    logger.info(f"Saved to {output_path}")

    # Summary
    feature_cols = [c for c in combined.columns
                    if c not in ['fraud_type', 'source']]
    print(f"\nTotal features: {len(feature_cols)}")
    print(f"Handcrafted features: 22")
    print(f"TF-IDF features: {len([c for c in combined.columns if c.startswith('tfidf_')])}")
    print(f"\nFeature matrix shape: {combined.shape}")
    print(f"\nFraud type distribution:")
    print(combined['fraud_type'].value_counts().to_string())

    # Check for nulls
    null_counts = combined[feature_cols].isnull().sum()
    if null_counts.sum() > 0:
        print(f"\nWarning — null values found:")
        print(null_counts[null_counts > 0].to_string())
    else:
        print(f"\nNo null values in feature matrix.")
