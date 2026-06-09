from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ScanHistory(db.Model):
    """Stores every complaint scan result."""
    __tablename__ = 'scan_history'

    id             = db.Column(db.Integer, primary_key=True)
    scan_type      = db.Column(db.String(20), default='complaint')
    input_text     = db.Column(db.Text)
    title          = db.Column(db.String(255))
    prediction     = db.Column(db.String(50))
    confidence     = db.Column(db.Float)
    risk_score     = db.Column(db.Integer)
    all_probs      = db.Column(db.Text)
    processing_ms  = db.Column(db.Float)
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'scan_type':     self.scan_type,
            'title':         self.title or '',
            'input_text':    (self.input_text or '')[:120] + '...'
                             if len(self.input_text or '') > 120
                             else self.input_text,
            'prediction':    self.prediction,
            'confidence':    self.confidence,
            'risk_score':    self.risk_score,
            'timestamp':     self.timestamp.isoformat(),
            'processing_ms': self.processing_ms,
        }


class URLScan(db.Model):
    """Stores threat intelligence results for URLs."""
    __tablename__ = 'url_scans'

    id               = db.Column(db.Integer, primary_key=True)
    url              = db.Column(db.Text)
    domain           = db.Column(db.String(255))
    risk_score       = db.Column(db.Integer)
    risk_level       = db.Column(db.String(20))
    blacklist_status = db.Column(db.String(20))
    indicators       = db.Column(db.Text)
    registrar        = db.Column(db.String(255))
    domain_age_days  = db.Column(db.Integer)
    timestamp        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':               self.id,
            'url':              self.url,
            'domain':           self.domain,
            'risk_score':       self.risk_score,
            'risk_level':       self.risk_level,
            'blacklist_status': self.blacklist_status,
            'indicators':       self.indicators,
            'registrar':        self.registrar,
            'domain_age_days':  self.domain_age_days,
            'timestamp':        self.timestamp.isoformat(),
        }
