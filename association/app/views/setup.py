import os
from datetime import datetime, timezone
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash
from association.config import Config
from association.app.extensions import db
from association.app.models.user import User
from association.app.forms.auth import RegisterForm

bp = Blueprint('setup', __name__)

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    preset_password = os.getenv('SETUP_PASSWORD', 'ilovebing')
    form = RegisterForm()
    current_year = datetime.now(timezone.utc).year
    form.grade.choices = [(f'{year}级', f'{year}级') for year in range(current_year, current_year - 6, -1)]
    # We don't need department selection for the president
    form.department_id.choices = []

    if request.method == 'POST':
        setup_password = request.form.get('setup_password')
        if setup_password != preset_password:
            flash('设置密码不正确', 'danger')
            return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, form=form)

        host = request.form.get('host')
        port = request.form.get('port') or '3306'
        user = request.form.get('user')
        db_password = request.form.get('db_password')
        dbname = request.form.get('dbname')
        if host and user and dbname:
            url = f"mysql+pymysql://{user}:{db_password}@{host}:{port}/{dbname}?charset=utf8mb4"
            with open('.env', 'a') as f:
                f.write(f"\nDATABASE_URL={url}\n")

        if form.validate_on_submit():
            u = User.query.filter_by(student_id=form.student_id.data).first()

            existing_user_phone = User.query.filter(User.phone == form.phone.data, User.id != (u.id if u else None)).first()
            if existing_user_phone:
                flash('该手机号已被注册', 'danger')
                return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, form=form)

            existing_user_email = User.query.filter(User.email == form.email.data, User.id != (u.id if u else None)).first()
            if existing_user_email:
                flash('该邮箱已被注册', 'danger')
                return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, form=form)

            pw_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if u:
                u.name = form.name.data
                u.class_name = form.class_name.data
                u.gender = form.gender.data
                u.grade = form.grade.data
                u.phone = form.phone.data
                u.email = form.email.data
                u.password_hash = pw_hash
                u.role = 'president'
                u.registration_status = 'approved'
                u.is_active = True
                u.updated_at = datetime.now(timezone.utc)
            else:
                u = User(
                    student_id=form.student_id.data,
                    name=form.name.data,
                    class_name=form.class_name.data,
                    gender=form.gender.data,
                    grade=form.grade.data,
                    phone=form.phone.data,
                    email=form.email.data,
                    password_hash=pw_hash,
                    role='president',
                    registration_status='approved',
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.session.add(u)
            db.session.commit()
            flash('设置成功', 'success')
            return redirect(url_for('auth.login'))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text} - {error}", 'danger')

    return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, form=form)
