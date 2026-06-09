import sys
sys.path.insert(0, '/Users/devansh/Desktop/upi-fraud-analyzer')

import pytest
import json
from app import create_app
from src.api.database import db


@pytest.fixture
def client():
    """Create test Flask client with in-memory database."""
    app = create_app()
    app.config['TESTING']                    = True
    app.config['SQLALCHEMY_DATABASE_URI']    = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED']           = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        res  = client.get('/api/health')
        data = json.loads(res.data)
        assert res.status_code    == 200
        assert data['status']     == 'ok'
        assert data['service']    == 'UPI Fraud Analyzer API'

    def test_health_returns_scan_counts(self, client):
        res  = client.get('/api/health')
        data = json.loads(res.data)
        assert 'total_scans' in data
        assert 'total_urls'  in data


class TestPredictEndpoint:
    def test_predict_valid_complaint(self, client):
        res = client.post('/api/predict',
            json={'text': 'I received an OTP fraud call from fake bank claiming KYC update needed. Lost Rs 20000.'})
        data = json.loads(res.data)
        assert res.status_code      == 200
        assert 'prediction'         in data
        assert 'confidence'         in data
        assert 'risk_score'         in data
        assert 'all_probabilities'  in data
        assert 'scan_id'            in data

    def test_predict_returns_valid_fraud_type(self, client):
        res  = client.post('/api/predict',
            json={'text': 'I received an OTP fraud call. Lost Rs 20000.'})
        data = json.loads(res.data)
        valid_types = [
            'fake_collect_request', 'fake_kyc_freeze',
            'fake_merchant', 'investment_scam',
            'job_advance_fee', 'lottery_reward',
            'otp_relay', 'qr_swap',
        ]
        assert data['prediction'] in valid_types

    def test_predict_confidence_between_0_and_100(self, client):
        res  = client.post('/api/predict',
            json={'text': 'UPI fraud complaint about lost money'})
        data = json.loads(res.data)
        assert 0 <= data['confidence'] <= 100

    def test_predict_missing_text_returns_400(self, client):
        res = client.post('/api/predict', json={})
        assert res.status_code == 400

    def test_predict_short_text_returns_400(self, client):
        res = client.post('/api/predict', json={'text': 'hi'})
        assert res.status_code == 400

    def test_predict_with_title(self, client):
        res = client.post('/api/predict',
            json={
                'text':  'Scammer called and asked for OTP. Lost Rs 5000.',
                'title': 'OTP fraud complaint',
            })
        assert res.status_code == 200

    def test_predict_saves_to_database(self, client):
        client.post('/api/predict',
            json={'text': 'I lost Rs 30000 in UPI fraud via fake collect request'})
        res  = client.get('/api/history')
        data = json.loads(res.data)
        assert data['total'] >= 1


class TestTrendsEndpoint:
    def test_trends_returns_data(self, client):
        res  = client.get('/api/trends')
        data = json.loads(res.data)
        assert res.status_code          == 200
        assert 'fraud_type_counts'      in data
        assert 'total_records'          in data
        assert 'labelled_records'       in data

    def test_trends_has_all_fraud_types(self, client):
        res  = client.get('/api/trends')
        data = json.loads(res.data)
        expected = [
            'fake_collect_request', 'otp_relay',
            'qr_swap', 'investment_scam',
        ]
        for ft in expected:
            assert ft in data['fraud_type_counts']


class TestSearchEndpoint:
    def test_search_returns_results(self, client):
        res  = client.get('/api/search?q=otp')
        data = json.loads(res.data)
        assert res.status_code == 200
        assert 'results'       in data
        assert 'count'         in data

    def test_search_missing_query_returns_400(self, client):
        res = client.get('/api/search')
        assert res.status_code == 400

    def test_search_results_have_required_fields(self, client):
        res  = client.get('/api/search?q=upi&limit=3')
        data = json.loads(res.data)
        if data['results']:
            record = data['results'][0]
            assert 'title'      in record
            assert 'text'       in record
            assert 'fraud_type' in record
            assert 'source'     in record

    def test_search_respects_limit(self, client):
        res  = client.get('/api/search?q=fraud&limit=2')
        data = json.loads(res.data)
        assert len(data['results']) <= 2


class TestHistoryEndpoint:
    def test_history_returns_empty_initially(self, client):
        res  = client.get('/api/history')
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data['total']   >= 0
        assert isinstance(data['scans'], list)

    def test_history_grows_after_scan(self, client):
        client.post('/api/predict',
            json={'text': 'I lost money in UPI fraud via OTP sharing'})
        res  = client.get('/api/history')
        data = json.loads(res.data)
        assert data['total'] >= 1

    def test_history_records_have_required_fields(self, client):
        client.post('/api/predict',
            json={'text': 'Fake KYC update scam. Lost Rs 10000 via UPI.'})
        res    = client.get('/api/history')
        data   = json.loads(res.data)
        record = data['scans'][0]
        assert 'id'          in record
        assert 'prediction'  in record
        assert 'confidence'  in record
        assert 'risk_score'  in record
        assert 'timestamp'   in record


class TestStatsEndpoint:
    def test_stats_returns_counts(self, client):
        res  = client.get('/api/stats')
        data = json.loads(res.data)
        assert res.status_code   == 200
        assert 'total_scans'     in data
        assert 'total_urls'      in data
        assert 'critical_urls'   in data

    def test_stats_count_increases(self, client):
        client.post('/api/predict',
            json={'text': 'QR code was swapped at petrol pump. Lost Rs 1200.'})
        res  = client.get('/api/stats')
        data = json.loads(res.data)
        assert data['total_scans'] >= 1
