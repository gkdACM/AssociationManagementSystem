from association.app.extensions import db

class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)
    class_name = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.Enum('男', '女', '其他'), nullable=False)
    grade = db.Column(db.String(16), nullable=False)
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('system_admin', 'president', 'vice_president', 'minister', 'member'), nullable=False, default='member')
    registration_status = db.Column(db.Enum('pending', 'approved', 'rejected'), nullable=False, default='pending')
    registration_reason = db.Column(db.String(255))
    department_id = db.Column(db.BigInteger, db.ForeignKey('department.id'))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    department = db.relationship('Department', backref=db.backref('users', lazy='dynamic'))
