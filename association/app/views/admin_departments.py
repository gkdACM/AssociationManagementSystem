from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import Department, User
from association.app.utils.auth import roles_required, get_current_user_optional

bp = Blueprint('admin_departments', __name__, url_prefix='/admin')

@bp.route('/departments', methods=['GET', 'POST'])
@roles_required('president')
def departments():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        if name:
            d = Department(name=name, description=description, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            db.session.add(d)
            db.session.commit()
        return redirect(url_for('admin_departments.departments'))
    items = Department.query.order_by(Department.name.asc()).all()
    return render_template('admin/departments.html', items=items)

@bp.route('/departments/<int:dep_id>/delete', methods=['POST'])
@roles_required('president')
def delete_department(dep_id):
    d = db.session.get(Department, dep_id)
    if d:
        User.query.filter_by(department_id=dep_id).update({'department_id': None})
        db.session.delete(d)
        db.session.commit()
    return redirect(url_for('admin_departments.departments'))

@bp.route('/departments/<int:dep_id>/set-minister', methods=['POST'])
@roles_required('president')
def set_minister(dep_id):
    d = db.session.get(Department, dep_id)
    if not d:
        return redirect(url_for('admin_departments.departments'))
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_departments.departments'))
    u = User.query.filter_by(student_id=sid).first()
    if not u:
        return redirect(url_for('admin_departments.departments'))
    if u.role in ('president','vice_president'):
        return redirect(url_for('admin_departments.departments'))
    existing = User.query.filter_by(department_id=dep_id, role='minister').all()
    for ex in existing:
        if ex.id != u.id:
            ex.role = 'member'
            ex.updated_at = datetime.utcnow()
    u.role = 'minister'
    u.department_id = dep_id
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_departments.departments'))

@bp.route('/vice/set', methods=['POST'])
@roles_required('president')
def set_vice():
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_departments.departments'))
    count_vp = db.session.query(User).filter(User.role == 'vice_president').count()
    if count_vp >= 2:
        return redirect(url_for('admin_departments.departments'))
    u = User.query.filter_by(student_id=sid).first()
    if not u:
        return redirect(url_for('admin_departments.departments'))
    u.role = 'vice_president'
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_departments.departments'))

@bp.route('/vice/unset', methods=['POST'])
@roles_required('president')
def unset_vice():
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_departments.departments'))
    u = User.query.filter_by(student_id=sid, role='vice_president').first()
    if not u:
        return redirect(url_for('admin_departments.departments'))
    u.role = 'member'
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_departments.departments'))

@bp.route('/president/transfer', methods=['POST'])
@roles_required('president')
def transfer_president():
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_departments.departments'))
    current = get_current_user_optional()
    target = User.query.filter_by(student_id=sid).first()
    if not target or not current or target.id == current.id:
        return redirect(url_for('admin_departments.departments'))
    target.role = 'president'
    target.updated_at = datetime.utcnow()
    count_vp = db.session.query(User).filter(User.role == 'vice_president').count()
    if count_vp < 2:
        current.role = 'vice_president'
    else:
        current.role = 'member'
    current.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_departments.departments'))

@bp.route('/departments/<int:dep_id>/unset-minister', methods=['POST'])
@roles_required('president')
def unset_minister(dep_id):
    d = db.session.get(Department, dep_id)
    if not d:
        return redirect(url_for('admin_departments.departments'))
    ms = User.query.filter_by(department_id=dep_id, role='minister').all()
    for m in ms:
        m.role = 'member'
        m.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_departments.departments'))
