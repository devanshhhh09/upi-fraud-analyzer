import json
import time
import pandas as pd
from flask import Blueprint, request, jsonify
from src.api.database import db, ScanHistory, URLScan
from src.utils.logger import get_logger

logger = get_logger(__name__)
api_bp = Blueprint('api', __name__)


def get_model_components():
    """Lazy-load ML components."""
    import joblib
    import config
    from src.features.feature_extractor import extract_features
    from src.features.tfidf_vectorizer import clean_text

    model     = joblib.load(config.MODELS_DIR / 'random_forest.pkl')
    le        = joblib.load(config.MODELS_DIR / 'label_encoder.pkl')
    tfidf_vec = joblib.load(config.MODELS_DIR / 'tfidf_vectorizer.pkl')

    return model, le, tfidf_vec, extract_features, clean_text


# ── Health ────────────────────────────────────────────────────────────

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status':        'ok',
        'service':       'UPI Fraud Analyzer API',
        'version':       '1.0.0',
        'total_scans':   ScanHistory.query.count(),
        'total_urls':    URLScan.query.count(),
    })


# ── Predict ───────────────────────────────────────────────────────────

@api_bp.route('/predict', methods=['POST'])
def predict():
    start_time = time.time()
    data       = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing required field: text'}), 400

    text  = str(data.get('text', '')).strip()
    title = str(data.get('title', '')).strip()

    if len(text) < 10:
        return jsonify({'error': 'Text too short — minimum 10 characters'}), 400

    try:
        import config
        model, le, tfidf_vec, extract_features, clean_text = get_model_components()

        # Extract handcrafted features
        feats   = extract_features(text, title)
        feat_df = pd.DataFrame([feats])

        # TF-IDF features
        tfidf_mat  = tfidf_vec.transform([clean_text(f"{title} {text}")])
        tfidf_cols = [f'tfidf_{f}' for f in tfidf_vec.get_feature_names_out()]
        tfidf_df   = pd.DataFrame(tfidf_mat.toarray(), columns=tfidf_cols)

        # Combine and align
        combined = pd.concat([feat_df, tfidf_df], axis=1)
        model_features = (
            list(model.feature_names_in_)
            if hasattr(model, 'feature_names_in_')
            else list(combined.columns)
        )
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

        risk_score = min(100, int(
            confidence * 0.7 +
            feats.get('urgency_keyword_count', 0) * 5 +
            feats.get('has_amount', 0) * 10
        ))

        processing_ms = round((time.time() - start_time) * 1000, 1)

        # Save to database
        scan = ScanHistory(
            scan_type     = 'complaint',
            input_text    = text,
            prediction    = prediction,
            confidence    = confidence,
            risk_score    = risk_score,
            all_probs     = json.dumps(all_probs),
            processing_ms = processing_ms,
        )
        db.session.add(scan)
        db.session.commit()
        logger.info(f"Saved scan #{scan.id}: {prediction} ({confidence}%)")

        return jsonify({
            'prediction':         prediction,
            'confidence':         confidence,
            'risk_score':         risk_score,
            'all_probabilities':  all_probs,
            'processing_time_ms': processing_ms,
            'scan_id':            scan.id,
        })

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Intel ─────────────────────────────────────────────────────────────

@api_bp.route('/intel', methods=['POST'])
def intel():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400

    url = str(data['url']).strip()

    try:
        from src.threat_intel.intel_runner import full_intel_report
        result = full_intel_report(url)

        # Save to database
        url_scan = URLScan(
            url              = url,
            domain           = result['domain'],
            risk_score       = result['risk']['score'],
            risk_level       = result['risk']['risk_level'],
            blacklist_status = result['blacklist']['status'],
            indicators       = json.dumps(result['risk']['indicators']),
            registrar        = result['whois'].get('registrar', 'Unknown'),
            domain_age_days  = result['whois'].get('domain_age_days'),
        )
        db.session.add(url_scan)
        db.session.commit()
        logger.info(f"Saved URL scan #{url_scan.id}: {result['domain']} "
                    f"({result['risk']['risk_level']})")

        return jsonify({
            'url':               url,
            'domain':            result['domain'],
            'risk_score':        result['risk']['score'],
            'risk_level':        result['risk']['risk_level'],
            'indicators':        result['risk']['indicators'],
            'whois':             result['whois'],
            'dns':               result['dns'],
            'impersonation':     result['impersonation'],
            'blacklist_status':  result['blacklist']['status'],
            'blacklist_sources': result['blacklist']['found_in'],
            'scan_id':           url_scan.id,
        })

    except Exception as e:
        logger.error(f"Intel error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Trends ────────────────────────────────────────────────────────────

@api_bp.route('/trends', methods=['GET'])
def trends():
    try:
        import config
        df       = pd.read_csv(config.RAW_DIR / 'dataset_raw.csv')
        labelled = df[df['fraud_type'] != 'unlabelled']
        counts   = labelled['fraud_type'].value_counts().to_dict()
        sources  = df['source'].value_counts().to_dict()

        # Add live scan counts from database
        live_scans = db.session.query(
            ScanHistory.prediction,
            db.func.count(ScanHistory.id)
        ).group_by(ScanHistory.prediction).all()

        live_counts = {pred: count for pred, count in live_scans}

        return jsonify({
            'fraud_type_counts': counts,
            'source_counts':     sources,
            'total_records':     len(df),
            'labelled_records':  len(labelled),
            'live_scan_counts':  live_counts,
            'total_scans_done':  ScanHistory.query.count(),
        })

    except Exception as e:
        logger.error(f"Trends error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Search ────────────────────────────────────────────────────────────

@api_bp.route('/search', methods=['GET'])
def search():
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
            'results': results[
                ['title', 'text', 'fraud_type', 'source']
            ].to_dict(orient='records'),
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


# ── History ───────────────────────────────────────────────────────────

@api_bp.route('/history', methods=['GET'])
def history():
    """Return scan history from database."""
    try:
        limit = int(request.args.get('limit', 50))
        scans = ScanHistory.query.order_by(
            ScanHistory.timestamp.desc()
        ).limit(limit).all()

        url_scans = URLScan.query.order_by(
            URLScan.timestamp.desc()
        ).limit(20).all()

        return jsonify({
            'scans':     [s.to_dict() for s in scans],
            'url_scans': [u.to_dict() for u in url_scans],
            'total':     ScanHistory.query.count(),
        })

    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Stats ─────────────────────────────────────────────────────────────

@api_bp.route('/stats', methods=['GET'])
def stats():
    """Summary statistics for dashboard."""
    try:
        total_scans   = ScanHistory.query.count()
        total_urls    = URLScan.query.count()
        critical_urls = URLScan.query.filter_by(risk_level='CRITICAL').count()
        high_risk     = URLScan.query.filter(
            URLScan.risk_score >= 50
        ).count()

        top_fraud = db.session.query(
            ScanHistory.prediction,
            db.func.count(ScanHistory.id).label('count')
        ).group_by(
            ScanHistory.prediction
        ).order_by(
            db.func.count(ScanHistory.id).desc()
        ).first()

        return jsonify({
            'total_scans':    total_scans,
            'total_urls':     total_urls,
            'critical_urls':  critical_urls,
            'high_risk_urls': high_risk,
            'top_fraud_type': top_fraud[0] if top_fraud else None,
        })

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500
