import json
import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)


def load_json_source(path, source_name):
    if not path.exists():
        logger.warning(f"File not found, skipping: {path}")
        return pd.DataFrame()
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    if not records:
        logger.warning(f"Empty file: {path}")
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["source"] = source_name
    logger.info(f"Loaded {len(df)} records from {source_name}")
    return df


def combine_all_sources():
    sources = [
        (config.RAW_DIR / "pib_articles.json",  "PIB"),
        (config.RAW_DIR / "reddit_posts.json",   "Reddit"),
        (config.RAW_DIR / "news_articles.json",  "NewsAPI"),
        (config.RAW_DIR / "seed_dataset.json",   "SeedData"),
    ]

    dfs = []
    for path, name in sources:
        df = load_json_source(path, name)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        logger.error("No data found. Run scrapers first.")
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)

    # Standardize column names
    combined = combined.rename(columns={
        "description": "text",
        "date":        "date_raw",
    })

    # Keep only essential columns
    keep = ["title", "text", "date_raw", "url", "source", "fraud_type"]
    combined = combined[[c for c in keep if c in combined.columns]]

    # Fill missing fraud_type with unlabelled
    if "fraud_type" not in combined.columns:
        combined["fraud_type"] = "unlabelled"
    else:
        combined["fraud_type"] = combined["fraud_type"].fillna("unlabelled")

    # Clean text
    combined = combined.dropna(subset=["text"])
    combined = combined[combined["text"].str.len() > 30]
    combined = combined.drop_duplicates(subset=["text"])

    output_path = config.RAW_DIR / "dataset_raw.csv"
    combined.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(f"Combined dataset: {len(combined)} records → {output_path}")
    return combined


if __name__ == "__main__":
    df = combine_all_sources()
    if not df.empty:
        print(f"\nTotal records: {len(df)}")
        print(f"\nSource breakdown:")
        print(df["source"].value_counts().to_string())
        print(f"\nFraud type breakdown:")
        print(df["fraud_type"].value_counts().to_string())
