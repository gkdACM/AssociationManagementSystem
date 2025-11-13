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
        # 登录后如果为默认重置密码，强制跳转到修改密码页面
        default_pw = check_password('123456', user.password_hash)
        target = 'auth.change_password' if default_pw else 'home.index'
        resp = make_response(redirect(url_for(target)))
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

@bp.route('/me/password', methods=['GET','POST'])
def change_password():
    uid = session.get('uid')
    if not uid:
        try:
            verify_jwt_in_request(optional=True)
            uid = get_jwt_identity()
        except Exception:
            uid = None
    if not uid:
        return redirect(url_for('auth.login'))
    user = db.session.get(User, uid)
    if request.method == 'POST':
        current = (request.form.get('current_password') or '').strip()
        newpw = (request.form.get('new_password') or '').strip()
        confirm = (request.form.get('confirm_password') or '').strip()
        if not current or not newpw or not confirm:
            return render_template('auth/change_password.html', error='请填写所有字段')
        if not check_password(current, user.password_hash):
            return render_template('auth/change_password.html', error='当前密码不正确')
        if len(newpw) < 6:
            return render_template('auth/change_password.html', error='新密码长度至少为6位')
        if newpw != confirm:
            return render_template('auth/change_password.html', error='两次输入的新密码不一致')
        user.password_hash = hash_password(newpw)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        from flask import make_response, flash
        flash('密码已更新，请重新登录')
        resp = make_response(redirect(url_for('auth.login')))
        unset_jwt_cookies(resp)
        session.clear()
        return resp
    return render_template('auth/change_password.html')
