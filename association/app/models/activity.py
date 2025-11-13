from association.app.extensions import db

class Activity(db.Model):
    __tablename__ = 'activity'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    department_id = db.Column(db.BigInteger, db.ForeignKey('department.id'))
    leader_user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'))
    event_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    department = db.relationship('Department', backref=db.backref('activities', lazy='dynamic'))
    leader = db.relationship('User', backref=db.backref('leading_activities', lazy='dynamic'), foreign_keys=[leader_user_id])

class ActivityApplication(db.Model):
    __tablename__ = 'activity_application'
    id = db.Column(db.BigInteger, primary_key=True)
    activity_id = db.Column(db.BigInteger, db.ForeignKey('activity.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('pending','approved','rejected'), nullable=False, default='pending')
    remark = db.Column(db.String(255))
    applied_at = db.Column(db.DateTime, nullable=False)
    decided_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('activity_id','user_id', name='uniq_activity_user'),)
    activity = db.relationship('Activity', backref=db.backref('applications', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('activity_applications', lazy='dynamic'))
