from association.app.extensions import db

class RegistrationAudit(db.Model):
    __tablename__ = 'registration_audit'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.Enum('approve', 'reject'), nullable=False)
    reason = db.Column(db.String(255))
    operator_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, nullable=False)

class UserProfileHistory(db.Model):
    __tablename__ = 'user_profile_history'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    changes = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), nullable=False)
    approver_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    decided_at = db.Column(db.DateTime)

class LeaveApplication(db.Model):
    __tablename__ = 'leave_application'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.Enum('pending','approved','rejected'), nullable=False)
    operator_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, nullable=False)
    decided_at = db.Column(db.DateTime)
