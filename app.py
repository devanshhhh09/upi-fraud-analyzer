import os
from flask import Flask, jsonify
from flask_cors import CORS
from src.api.database import db
from src.api.routes import api_bp
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    """Application factory — creates and configures Flask app."""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY']             = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///upi_fraud.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS']         = False

    # Extensions
    CORS(app)
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'service':  'UPI Fraud Pattern Analyzer',
            'version':  '1.0.0',
            'status':   'running',
            'endpoints': [
                'GET  /api/health',
                'POST /api/predict',
                'POST /api/intel',
                'GET  /api/trends',
                'GET  /api/search?q=keyword',
            ]
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == '__main__':
    app = create_app()
    logger.info("Starting UPI Fraud Analyzer API...")
    app.run(debug=True, host='0.0.0.0', port=5001)
