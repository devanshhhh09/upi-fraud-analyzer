#!/bin/bash
set -e

echo "=== UPI Fraud Analyzer Build Script ==="

export PYTHONPATH=/opt/render/project/src

# Create directories
mkdir -p data/raw data/processed data/features models reports/briefs instance

echo "--- Generating seed dataset ---"
python -m src.ingestion.seed_data_generator

echo "--- Creating dataset_raw.csv from seed data ---"
python3 -c "
import json
import pandas as pd
from pathlib import Path

raw_dir = Path('data/raw')

# Load seed dataset
with open(raw_dir / 'seed_dataset.json') as f:
    records = json.load(f)

df = pd.DataFrame(records)
df['source']   = 'SeedData'
df['date_raw'] = '2024-01-01'
df['url']      = ''
df = df.rename(columns={'description': 'text'})
keep = ['title', 'text', 'date_raw', 'url', 'source', 'fraud_type']
df   = df[[c for c in keep if c in df.columns]]
df.to_csv(raw_dir / 'dataset_raw.csv', index=False)
print(f'dataset_raw.csv created: {len(df)} records')
"

echo "--- Building features ---"
python -m src.features.build_features

echo "--- Training models ---"
python -m src.models.trainer

echo "--- Build complete ---"
ls -la models/
