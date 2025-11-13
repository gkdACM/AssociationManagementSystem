from association.app.extensions import db

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    department_id = db.Column(db.BigInteger, db.ForeignKey('department.id'))
    leader_user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    github_url = db.Column(db.String(255))
    status = db.Column(db.Enum('draft','active','pending_acceptance','accepted','rejected'), nullable=False, default='draft')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    department = db.relationship('Department', backref=db.backref('projects', lazy='dynamic'))
    leader = db.relationship('User', backref=db.backref('leading_projects', lazy='dynamic'), foreign_keys=[leader_user_id])

class ProjectParticipation(db.Model):
    __tablename__ = 'project_participation'
    id = db.Column(db.BigInteger, primary_key=True)
    project_id = db.Column(db.BigInteger, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum('pending','approved','rejected'), nullable=False, default='pending')
    remark = db.Column(db.String(255))
    applied_at = db.Column(db.DateTime, nullable=False)
    decided_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('project_id','user_id', name='uniq_project_user'),)
    project = db.relationship('Project', backref=db.backref('participations', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('project_participations', lazy='dynamic'))

