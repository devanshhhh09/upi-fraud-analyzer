import time
import pandas as pd
from flask import Blueprint, request, jsonify
from src.utils.logger import get_logger

logger = get_logger(__name__)
api_bp = Blueprint('api', __name__)


def get_components():
    """
    Lazy-load all ML components.
    Avoids loading models at import time.
    """
    import joblib
    import config
    from src.features.feature_extractor import extract_features
    from src.models.explainer import FraudExplainer
    from src.threat_intel.intel_runner import full_intel_report

    components = {}

    try:
        components['model']   = joblib.load(config.MODELS_DIR / 'random_forest.pkl')
        components['le']      = joblib.load(config.MODELS_DIR / 'label_encoder.pkl')
        components['extract'] = extract_features
        logger.info("ML components loaded")
    except Exception as e:
        logger.error(f"Failed to load ML components: {e}")

    components['intel'] = full_intel_report
    return components


# ── Health check ──────────────────────────────────────────────────────

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status':  'ok',
        'service': 'UPI Fraud Analyzer API',
        'version': '1.0.0',
    })


# ── Fraud prediction ──────────────────────────────────────────────────

@api_bp.route('/predict', methods=['POST'])
def predict():
    """
    Classify a complaint text as a fraud type.

    Request body:
        {
            "text": "I received a collect request...",
            "title": "Optional title"
        }

    Response:
        {
            "prediction": "fake_collect_request",
            "confidence": 85.0,
            "risk_score": 78,
            "all_probabilities": {...},
            "top_reasons": [...],
            "processing_time_ms": 12
        }
    """
    start_time = time.time()
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing required field: text'}), 400

    text  = str(data.get('text', '')).strip()
    title = str(data.get('title', '')).strip()

    if len(text) < 10:
        return jsonify({'error': 'Text too short — minimum 10 characters'}), 400

    try:
        components = get_components()
        model      = components['model']
        le         = components['le']
        extract    = components['extract']

        # Extract features
        feats    = extract(text, title)
        feat_df  = pd.DataFrame([feats])

        # Align with training features
        import joblib
        import config
        tfidf_vec = joblib.load(config.MODELS_DIR / 'tfidf_vectorizer.pkl')
        from src.features.tfidf_vectorizer import clean_text
        tfidf_mat = tfidf_vec.transform([clean_text(f"{title} {text}")])
        tfidf_cols = [f'tfidf_{f}' for f in tfidf_vec.get_feature_names_out()]
        tfidf_df   = pd.DataFrame(tfidf_mat.toarray(), columns=tfidf_cols)

        # Combine
        combined = pd.concat([feat_df, tfidf_df], axis=1)

        # Get model feature names
        model_features = model.feature_names_in_ \
            if hasattr(model, 'feature_names_in_') else combined.columns.tolist()

        for col in model_features:
            if col not in combined.columns:
                combined[col] = 0
        combined = combined[model_features].fillna(0)

        # Predict
        pred_encoded = model.predict(combined)[0]
        pred_proba   = model.predict_proba(combined)[0]
        prediction   = le.inverse_transform([pred_encoded])[0]
        confidence   = round(float(pred_proba[pred_encoded]) * 100, 1)

        all_probs = {
            le.inverse_transform([i])[0]: round(float(p) * 100, 1)
            for i, p in enumerate(pred_proba)
        }

        # Risk score (0-100 based on confidence + keyword signals)
        risk_score = min(100, int(
            confidence * 0.7 +
            feats.get('urgency_keyword_count', 0) * 5 +
            feats.get('has_amount', 0) * 10
        ))

        processing_ms = round((time.time() - start_time) * 1000, 1)

        return jsonify({
            'prediction':        prediction,
            'confidence':        confidence,
            'risk_score':        risk_score,
            'all_probabilities': all_probs,
            'processing_time_ms': processing_ms,
        })

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Threat intelligence ───────────────────────────────────────────────

@api_bp.route('/intel', methods=['POST'])
def intel():
    """
    Run threat intelligence on a URL or domain.

    Request body:
        {"url": "https://sbi-kyc-update.xyz"}

    Response:
        {
            "domain": "sbi-kyc-update.xyz",
            "risk_score": 85,
            "risk_level": "CRITICAL",
            "indicators": [...],
            "whois": {...},
            "blacklist_status": "NOT FOUND"
        }
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400

    url = str(data['url']).strip()

    try:
        components = get_components()
        result     = components['intel'](url)

        return jsonify({
            'url':              url,
            'domain':           result['domain'],
            'risk_score':       result['risk']['score'],
            'risk_level':       result['risk']['risk_level'],
            'indicators':       result['risk']['indicators'],
            'whois':            result['whois'],
            'dns':              result['dns'],
            'impersonation':    result['impersonation'],
            'blacklist_status': result['blacklist']['status'],
            'blacklist_sources': result['blacklist']['found_in'],
        })

    except Exception as e:
        logger.error(f"Intel error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Trends ────────────────────────────────────────────────────────────

@api_bp.route('/trends', methods=['GET'])
def trends():
    """
    Return fraud type distribution from the dataset.
    Used by the dashboard for charts.
    """
    try:
        import config
        df = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
        labelled = df[df['fraud_type'] != 'unlabelled']
        counts   = labelled['fraud_type'].value_counts().to_dict()
        sources  = df['source'].value_counts().to_dict()

        return jsonify({
            'fraud_type_counts': counts,
            'source_counts':     sources,
            'total_records':     len(df),
            'labelled_records':  len(labelled),
        })

    except Exception as e:
        logger.error(f"Trends error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Dataset search ────────────────────────────────────────────────────

@api_bp.route('/search', methods=['GET'])
def search():
    """
    Search complaints by keyword.
    Query param: ?q=otp&limit=10
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))

    if not query:
        return jsonify({'error': 'Missing query parameter: q'}), 400

    try:
        import config
        df      = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
        mask    = df['text'].str.contains(query, case=False, na=False)
        results = df[mask].head(limit)

        return jsonify({
            'query':   query,
            'count':   int(mask.sum()),
            'results': results[['title', 'text', 'fraud_type', 'source']].to_dict(orient='records'),
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500
