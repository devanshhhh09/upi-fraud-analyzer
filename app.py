import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from src.api.database import db
from src.api.routes import api_bp
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']                    = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI']        = os.getenv(
        'DATABASE_URL', 'sqlite:///upi_fraud.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS']                 = False

    CORS(app)
    db.init_app(app)
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/scanner')
    def scanner():
        return render_template('scanner.html')

    @app.route('/intel')
    def intel():
        return render_template('intel.html')

    @app.route('/history')
    def history():
        return render_template('history.html')

    @app.route('/api')
    def api_root():
        return jsonify({
            'service':   'UPI Fraud Pattern Analyzer',
            'version':   '1.0.0',
            'endpoints': [
                'GET  /api/health',
                'POST /api/predict',
                'POST /api/intel',
                'GET  /api/trends',
                'GET  /api/search?q=keyword',
                'GET  /api/history',
                'GET  /api/stats',
            ]
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app


app = create_app()

if __name__ == '__main__':
    port  = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV', 'development') != 'production'
    logger.info(f"Starting UPI Fraud Analyzer API on port {port}...")
    app.run(debug=debug, host='0.0.0.0', port=port)
