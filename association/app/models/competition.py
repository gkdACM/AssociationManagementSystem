from association.app.extensions import db

class Competition(db.Model):
    __tablename__ = 'competition'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.Enum('internal','external'), nullable=False)
    level = db.Column(db.Enum('国际级','国家级','区域级','省级','市级','校级','联合赛','企业赛','邀请赛'), nullable=False)
    department_id = db.Column(db.BigInteger, db.ForeignKey('department.id'))
    event_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    department = db.relationship('Department', backref=db.backref('competitions', lazy='dynamic'))

class CompetitionResult(db.Model):
    __tablename__ = 'competition_result'
    id = db.Column(db.BigInteger, primary_key=True)
    competition_id = db.Column(db.BigInteger, db.ForeignKey('competition.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Numeric(6, 2))
    award = db.Column(db.String(64))
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (db.UniqueConstraint('competition_id', 'user_id', name='uniq_competition_user'),)
    competition = db.relationship('Competition', backref=db.backref('results', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('competition_results', lazy='dynamic'))

