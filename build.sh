#!/bin/bash
set -e

echo "=== UPI Fraud Analyzer Build Script ==="

# Set Python path
export PYTHONPATH=/opt/render/project/src

# Create directories
mkdir -p data/raw data/processed data/features models reports/briefs instance

echo "--- Generating seed dataset ---"
python -m src.ingestion.seed_data_generator

echo "--- Building features ---"
python -m src.features.build_features

echo "--- Training models ---"
python -m src.models.trainer

echo "--- Build complete ---"
ls -la models/
ls -la data/features/
