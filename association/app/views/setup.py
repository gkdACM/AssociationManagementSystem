import os
from datetime import datetime, timezone
import bcrypt
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from association.config import Config
from association.app.extensions import db
from association.app.models.user import User

bp = Blueprint('setup', __name__)

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    preset_password = os.getenv('SETUP_PASSWORD', 'ilovebing')
    current_year = datetime.now(timezone.utc).year
    grades = [(f'{year}级', f'{year}级') for year in range(current_year, current_year - 6, -1)]
    if request.method == 'POST':
        setup_password = request.form.get('setup_password')
        if setup_password != preset_password:
            flash('设置密码不正确', 'danger')
            return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)

        host = request.form.get('host')
        port = request.form.get('port') or '3306'
        user = request.form.get('user')
        password = request.form.get('password')
        dbname = request.form.get('dbname')
        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
        with open('.env', 'a') as f:
            f.write(f"\nDATABASE_URL={url}\n")
        admin_sid = request.form.get('admin_student_id')
        admin_name = request.form.get('admin_name')
        admin_class = request.form.get('admin_class_name')
        admin_gender = request.form.get('admin_gender')
        admin_grade = request.form.get('admin_grade')
        admin_phone = request.form.get('admin_phone')
        admin_email = request.form.get('admin_email')
        admin_pw = request.form.get('admin_password')

        if not re.match(r'^1\d{10}$', admin_phone):
            flash('手机号格式不正确', 'danger')
            return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)
        if not re.match(r'[^@]+@[^@]+\.[^@]+', admin_email):
            flash('邮箱格式不正确', 'danger')
            return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)

        if admin_sid and admin_name and admin_class and admin_gender and admin_grade and admin_pw:
            u = User.query.filter_by(student_id=admin_sid).first()

            # Check for phone and email uniqueness
            existing_user_phone = User.query.filter(User.phone == admin_phone, User.id != (u.id if u else None)).first()
            if existing_user_phone:
                flash('该手机号已被注册', 'danger')
                return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)

            existing_user_email = User.query.filter(User.email == admin_email, User.id != (u.id if u else None)).first()
            if existing_user_email:
                flash('该邮箱已被注册', 'danger')
                return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)

            pw_hash = bcrypt.hashpw(admin_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if u:
                u.name = admin_name
                u.class_name = admin_class
                u.gender = admin_gender
                u.grade = admin_grade
                u.phone = admin_phone
                u.email = admin_email
                u.password_hash = pw_hash
                u.role = 'president'
                u.registration_status = 'approved'
                u.is_active = True
                u.updated_at = datetime.now(timezone.utc)
            else:
                u = User(
                    student_id=admin_sid,
                    name=admin_name,
                    class_name=admin_class,
                    gender=admin_gender,
                    grade=admin_grade,
                    phone=admin_phone,
                    email=admin_email,
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
        flash('请填写所有管理员信息', 'danger')
        return redirect(url_for('home.index'))
    return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI, grades=grades)
