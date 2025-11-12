import os
from datetime import datetime
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for
from association.config import Config
from association.app.extensions import db
from association.app.models.user import User

bp = Blueprint('setup', __name__)

@bp.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
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
        if admin_sid and admin_name and admin_class and admin_gender and admin_grade and admin_pw:
            u = User.query.filter_by(student_id=admin_sid).first()
            pw_hash = bcrypt.hashpw(admin_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if u:
                u.name = admin_name
                u.class_name = admin_class
                u.gender = admin_gender
                u.grade = admin_grade
                u.phone = admin_phone
                u.email = admin_email
                u.password_hash = pw_hash
                u.role = 'system_admin'
                u.registration_status = 'approved'
                u.is_active = True
                u.updated_at = datetime.utcnow()
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
                    role='system_admin',
                    registration_status='approved',
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(u)
            db.session.commit()
            return redirect(url_for('auth.login'))
        return redirect(url_for('home.index'))
    return render_template('setup.html', database_url=Config.SQLALCHEMY_DATABASE_URI)
