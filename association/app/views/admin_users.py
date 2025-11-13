from datetime import datetime
import io, csv
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.audit import RegistrationAudit, LeaveApplication, UserProfileHistory
from association.app.models.points import PointsLedger
from association.app.models.project import ProjectParticipation
from association.app.models.exam import ExamResult
from association.app.models.competition import CompetitionResult
from association.app.views.auth import hash_password
from association.app.utils.auth import roles_required, get_current_user_optional

bp = Blueprint('admin_users', __name__, url_prefix='/admin')

@bp.route('/users', methods=['GET'])
@roles_required('president', 'vice_president')
def users():
    dep = request.args.get('department_id', type=int)
    grade = request.args.get('grade')
    q = User.query
    if dep:
        q = q.filter(User.department_id == dep)
    if grade:
        q = q.filter(User.grade == grade)
    items = q.order_by(User.created_at.desc()).all()
    deps = Department.query.order_by(Department.name).all()
    grades = [g[0] for g in db.session.query(User.grade).distinct().all()]
    return render_template('admin/users.html', items=items, deps=deps, grades=grades)

@bp.route('/users/<int:user_id>/disable', methods=['POST'])
@roles_required('president', 'vice_president')
def disable_user(user_id):
    u = db.session.get(User, user_id)
    if u:
        if u.role in ('president', 'vice_president', 'minister'):
            return redirect(url_for('admin_users.users'))
        u.is_active = not u.is_active
        u.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/import', methods=['POST'])
@roles_required('president', 'vice_president')
def import_users():
    f = request.files.get('file')
    if not f:
        return redirect(url_for('admin_users.users'))
    data = f.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(data))
    for row in reader:
        sid = row.get('student_id')
        if not sid:
            continue
        u = User.query.filter_by(student_id=sid).first()
        dep_name = row.get('department')
        dep_id = None
        if dep_name:
            dep = Department.query.filter_by(name=dep_name).first()
            dep_id = dep.id if dep else None
        fields = {
            'name': row.get('name'),
            'class_name': row.get('class_name'),
            'gender': row.get('gender') or '其他',
            'grade': row.get('grade'),
            'department_id': dep_id,
            'is_active': (row.get('is_active') == '1'),
            'updated_at': datetime.utcnow(),
        }
        if u:
            for k, v in fields.items():
                if v is not None:
                    setattr(u, k, v)
        else:
            from association.app.views.auth import hash_password
            u = User(student_id=sid, created_at=datetime.utcnow(), registration_status='approved', password_hash=hash_password('123456'), **fields)
            db.session.add(u)
    db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/export', methods=['GET'])
@roles_required('president', 'vice_president')
def export_users():
    items = User.query.order_by(User.created_at.desc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['student_id','name','class_name','gender','grade','department','role','is_active','created_at'])
    for u in items:
        dep = db.session.get(Department, u.department_id) if u.department_id else None
        role_cn = '成员'
        if u.role == 'president':
            role_cn = '会长'
        elif u.role == 'vice_president':
            role_cn = '副会长'
        elif u.role == 'minister':
            role_cn = f"{dep.name if dep else ''}部长".strip()
        w.writerow([u.student_id,u.name,u.class_name,u.gender,u.grade, dep.name if dep else '', role_cn, 1 if u.is_active else 0, u.created_at])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='users.csv')

@bp.route('/users/disable-by-grade', methods=['POST'])
@roles_required('president', 'vice_president')
def disable_by_grade():
    grade = request.form.get('grade')
    if grade:
        now = datetime.utcnow()
        db.session.query(User).filter(User.grade == grade, User.role.notin_(('president','vice_president'))).update({'is_active': False, 'updated_at': now})
        db.session.commit()
    return redirect(url_for('admin_users.users', grade=grade))

@bp.route('/users/enable-by-grade', methods=['POST'])
@roles_required('president', 'vice_president')
def enable_by_grade():
    grade = request.form.get('grade')
    if grade:
        now = datetime.utcnow()
        db.session.query(User).filter(User.grade == grade).update({'is_active': True, 'updated_at': now})
        db.session.commit()
    return redirect(url_for('admin_users.users', grade=grade))

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@roles_required('president', 'vice_president')
def delete_user(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return redirect(url_for('admin_users.users'))
    if u.role in ('president','vice_president','minister'):
        return redirect(url_for('admin_users.users'))
    db.session.query(CompetitionResult).filter(CompetitionResult.user_id == user_id).delete(synchronize_session=False)
    db.session.query(ExamResult).filter(ExamResult.user_id == user_id).delete(synchronize_session=False)
    db.session.query(ProjectParticipation).filter(ProjectParticipation.user_id == user_id).delete(synchronize_session=False)
    db.session.query(PointsLedger).filter(PointsLedger.user_id == user_id).delete(synchronize_session=False)
    db.session.query(UserProfileHistory).filter(UserProfileHistory.user_id == user_id).delete(synchronize_session=False)
    db.session.query(LeaveApplication).filter(LeaveApplication.user_id == user_id).delete(synchronize_session=False)
    db.session.query(RegistrationAudit).filter(RegistrationAudit.user_id == user_id).delete(synchronize_session=False)
    db.session.delete(u)
    db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@roles_required('president','vice_president','minister')
def reset_password(user_id):
    current = get_current_user_optional()
    u = db.session.get(User, user_id)
    if not u:
        return redirect(url_for('admin_users.users'))
    # 部长只能重置本部门成员密码
    if current.role == 'minister':
        if not u.department_id or u.department_id != current.department_id:
            return redirect(url_for('admin_users.users'))
        if u.role in ('president','vice_president','minister'):
            return redirect(url_for('admin_users.users'))
    u.password_hash = hash_password('123456')
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/reset-all', methods=['POST'])
@roles_required('president','vice_president')
def reset_all_passwords():
    now = datetime.utcnow()
    users = User.query.all()
    for u in users:
        u.password_hash = hash_password('123456')
        u.updated_at = now
    db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/set-vice', methods=['POST'])
@roles_required('president')
def set_vice():
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_users.users'))
    count_vp = db.session.query(User).filter(User.role == 'vice_president').count()
    if count_vp >= 2:
        return redirect(url_for('admin_users.users'))
    u = User.query.filter_by(student_id=sid).first()
    if not u:
        return redirect(url_for('admin_users.users'))
    u.role = 'vice_president'
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_users.users'))

@bp.route('/users/unset-vice', methods=['POST'])
@roles_required('president')
def unset_vice():
    sid = (request.form.get('student_id') or '').strip()
    if not sid:
        return redirect(url_for('admin_users.users'))
    u = User.query.filter_by(student_id=sid, role='vice_president').first()
    if not u:
        return redirect(url_for('admin_users.users'))
    u.role = 'member'
    u.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_users.users'))

# 会长转让已迁移至部门管理页

@bp.route('/reviews', methods=['GET'])
@roles_required('president', 'vice_president')
def reviews():
    joins = User.query.filter_by(registration_status='pending').order_by(User.created_at.asc()).all()
    leaves = LeaveApplication.query.filter_by(status='pending').order_by(LeaveApplication.created_at.asc()).all()
    for la in leaves:
        la.user = db.session.get(User, la.user_id)
    return render_template('admin/reviews.html', joins=joins, leaves=leaves)

@bp.route('/reviews/registrations/<int:user_id>/approve', methods=['POST'])
@roles_required('president', 'vice_president')
def approve_registration(user_id):
    u = db.session.get(User, user_id)
    if u and u.registration_status == 'pending':
        u.registration_status = 'approved'
        u.updated_at = datetime.utcnow()
        db.session.add(RegistrationAudit(user_id=u.id, action='approve', operator_id=u.id, created_at=datetime.utcnow()))
        db.session.commit()
    return redirect(url_for('admin_users.reviews'))

@bp.route('/reviews/registrations/<int:user_id>/reject', methods=['POST'])
@roles_required('president', 'vice_president')
def reject_registration(user_id):
    u = db.session.get(User, user_id)
    reason = request.form.get('reason')
    if u and u.registration_status == 'pending':
        u.registration_status = 'rejected'
        u.registration_reason = reason
        u.updated_at = datetime.utcnow()
        db.session.add(RegistrationAudit(user_id=u.id, action='reject', reason=reason, operator_id=u.id, created_at=datetime.utcnow()))
        db.session.commit()
    return redirect(url_for('admin_users.reviews'))

@bp.route('/reviews/leaves/<int:leave_id>/approve', methods=['POST'])
@roles_required('president', 'vice_president')
def approve_leave(leave_id):
    la = db.session.get(LeaveApplication, leave_id)
    if la and la.status == 'pending':
        u = db.session.get(User, la.user_id)
        if u:
            u.is_active = False
            u.department_id = None
            u.updated_at = datetime.utcnow()
        la.status = 'approved'
        la.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('admin_users.reviews'))

@bp.route('/reviews/leaves/<int:leave_id>/reject', methods=['POST'])
@roles_required('president', 'vice_president')
def reject_leave(leave_id):
    la = db.session.get(LeaveApplication, leave_id)
    if la and la.status == 'pending':
        la.status = 'rejected'
        la.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('admin_users.reviews'))

@bp.route('/reviews/approve_all', methods=['POST'])
@roles_required('president', 'vice_president')
def approve_all_reviews():
    now = datetime.utcnow()
    joins = User.query.filter_by(registration_status='pending').all()
    for u in joins:
        u.registration_status = 'approved'
        u.updated_at = now
        db.session.add(RegistrationAudit(user_id=u.id, action='approve', operator_id=u.id, created_at=now))
    leaves = LeaveApplication.query.filter_by(status='pending').all()
    for la in leaves:
        la.status = 'approved'
        la.decided_at = now
        u = db.session.get(User, la.user_id)
        if u:
            u.is_active = False
            u.department_id = None
            u.updated_at = now
    db.session.commit()
    return redirect(url_for('admin_users.reviews'))
