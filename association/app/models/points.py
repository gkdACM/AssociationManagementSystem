from association.app.extensions import db

class Level(db.Model):
    __tablename__ = 'level'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    threshold_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

class PointsLedger(db.Model):
    __tablename__ = 'points_ledger'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    source_type = db.Column(db.Enum('exam', 'activity', 'manual'), nullable=False)
    source_id = db.Column(db.BigInteger)
    points = db.Column(db.Integer, nullable=False)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)

