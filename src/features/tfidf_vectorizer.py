import pandas as pd
import numpy as np
import joblib
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

# Words to remove from TF-IDF — noise identified in EDA
NOISE_WORDS = [
    'chars', 'http', 'https', 'www', 'com', 'html',
    'said', 'also', 'one', 'two', 'three', 'get', 'got',
]


def clean_text(text: str) -> str:
    """
    Clean text before TF-IDF vectorization.
    Removes URLs, special characters, noise words.
    """
    text = str(text).lower()

    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)

    # Remove special characters keeping spaces
    text = re.sub(r'[^a-z\s]', ' ', text)

    # Remove noise words identified in EDA
    for noise in NOISE_WORDS:
        text = re.sub(r'\b' + noise + r'\b', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def build_tfidf_features(
    df: pd.DataFrame,
    max_features: int = 500,
    save_vectorizer: bool = True,
) -> tuple[pd.DataFrame, TfidfVectorizer]:
    """
    Build TF-IDF feature matrix from text column.

    Args:
        df: DataFrame with 'text' column
        max_features: maximum number of TF-IDF features
        save_vectorizer: whether to save fitted vectorizer to disk

    Returns:
        tfidf_df: DataFrame of TF-IDF features
        vectorizer: fitted TfidfVectorizer
    """
    logger.info("Cleaning text for TF-IDF...")
    texts = df['text'].astype(str).apply(clean_text).tolist()

    logger.info(f"Fitting TF-IDF vectorizer (max_features={max_features})...")
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),       # unigrams and bigrams
        min_df=2,                  # ignore terms in fewer than 2 docs
        max_df=0.95,               # ignore terms in more than 95% of docs
        sublinear_tf=True,         # apply log normalization
        strip_accents='unicode',
    )

    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = [f'tfidf_{f}' for f in vectorizer.get_feature_names_out()]
    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=feature_names
    )

    logger.info(f"TF-IDF matrix shape: {tfidf_df.shape}")

    if save_vectorizer:
        vec_path = config.MODELS_DIR / 'tfidf_vectorizer.pkl'
        vec_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(vectorizer, vec_path)
        logger.info(f"Vectorizer saved to {vec_path}")

    return tfidf_df, vectorizer


if __name__ == "__main__":
    df = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
    tfidf_df, vectorizer = build_tfidf_features(df)

    print(f"\nTF-IDF matrix shape: {tfidf_df.shape}")
    print(f"\nTop 20 TF-IDF features:")
    feature_scores = tfidf_df.mean().sort_values(ascending=False)
    print(feature_scores.head(20).to_string())
