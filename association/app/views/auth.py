from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.forms.auth import LoginForm, RegisterForm
import bcrypt

bp = Blueprint('auth', __name__, url_prefix='')

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(student_id=form.data['student_id']).first()
        if not user or not check_password(form.data['password'], user.password_hash):
            return render_template('auth/login.html', form=form, error='账号或密码错误')
        if user.registration_status != 'approved' or not user.is_active:
            return render_template('auth/login.html', form=form, error='账号未审核或已禁用')
        token = create_access_token(identity=user.id)
        from flask import make_response
        resp = make_response(redirect(url_for('home.index')))
        set_access_cookies(resp, token)
        session['uid'] = user.id
        return resp
    return render_template('auth/login.html', form=form)

@bp.route('/logout', methods=['POST'])
def logout():
    from flask import make_response
    resp = make_response(redirect(url_for('home.index')))
    unset_jwt_cookies(resp)
    session.clear()
    return resp

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    form.department_id.choices = [(0, '不选择')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        if User.query.filter_by(student_id=form.data['student_id']).first():
            return render_template('auth/register.html', form=form, error='该学号已存在')
        dep_id = form.data['department_id'] or 0
        user = User(
            student_id=form.data['student_id'],
            name=form.data['name'],
            class_name=form.data['class_name'],
            gender=form.data['gender'],
            grade=form.data['grade'],
            phone=form.data['phone'],
            email=form.data['email'],
            password_hash=hash_password(form.data['password']),
            role='member',
            registration_status='pending',
            department_id=None if dep_id == 0 else dep_id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

@bp.route('/auth/debug')
def auth_debug():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
    except Exception:
        uid = None
    user = User.query.get(uid) if uid else None
    return render_template('auth/debug.html', user=user, uid=uid)
