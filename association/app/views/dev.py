from datetime import datetime, date
from flask import Blueprint, redirect, url_for, session
from flask_jwt_extended import create_access_token, set_access_cookies
from association.app.extensions import db
from association.app.models.user import User, Department

bp = Blueprint('dev', __name__, url_prefix='/dev')

@bp.route('/seed')
def seed():
    dep = Department.query.filter_by(name='开发部').first()
    if not dep:
        dep = Department(name='开发部', description='示例部门', created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        db.session.add(dep)
    admin = User.query.filter_by(student_id='A0001').first()
    if not admin:
        admin = User(
            student_id='A0001',
            name='系统管理员',
            class_name='计科-示例班级',
            gender='男',
            grade='2022',
            phone='13800000000',
            email='admin@example.com',
            password_hash='x',
            role='president',
            registration_status='approved',
            department_id=dep.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(admin)
    db.session.commit()
    return redirect(url_for('dev.login_admin'))

@bp.route('/login_admin')
def login_admin():
    admin = User.query.filter_by(student_id='A0001').first()
    if not admin:
        return redirect(url_for('dev.seed'))
    token = create_access_token(identity=admin.id)
    from flask import make_response
    resp = make_response(redirect(url_for('admin_competitions.competitions')))
    set_access_cookies(resp, token)
    session['uid'] = admin.id
    return resp
