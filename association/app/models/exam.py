from association.app.extensions import db

class Exam(db.Model):
    __tablename__ = 'exam'
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(255))
    department_id = db.Column(db.BigInteger, db.ForeignKey('department.id'))
    exam_date = db.Column(db.Date, nullable=False)
    pass_threshold = db.Column(db.Numeric(5, 2))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    department = db.relationship('Department', backref=db.backref('exams', lazy='dynamic'))

class ExamResult(db.Model):
    __tablename__ = 'exam_result'
    id = db.Column(db.BigInteger, primary_key=True)
    exam_id = db.Column(db.BigInteger, db.ForeignKey('exam.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Numeric(6, 2), nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (db.UniqueConstraint('exam_id', 'user_id', name='uniq_exam_user'),)
    exam = db.relationship('Exam', backref=db.backref('results', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('exam_results', lazy='dynamic'))
