from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ScanHistory(db.Model):
    """Stores every URL and complaint scan for history tracking."""
    __tablename__ = 'scan_history'

    id              = db.Column(db.Integer, primary_key=True)
    scan_type       = db.Column(db.String(20))   # 'complaint' or 'url'
    input_text      = db.Column(db.Text)
    prediction      = db.Column(db.String(50))
    confidence      = db.Column(db.Float)
    risk_score      = db.Column(db.Integer)
    timestamp       = db.Column(db.DateTime, default=datetime.utcnow)
    processing_ms   = db.Column(db.Float)

    def to_dict(self):
        return {
            'id':            self.id,
            'scan_type':     self.scan_type,
            'input_text':    self.input_text[:100] + '...'
                             if len(self.input_text or '') > 100 else self.input_text,
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
    timestamp        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':               self.id,
            'url':              self.url,
            'domain':           self.domain,
            'risk_score':       self.risk_score,
            'risk_level':       self.risk_level,
            'blacklist_status': self.blacklist_status,
            'timestamp':        self.timestamp.isoformat(),
        }
