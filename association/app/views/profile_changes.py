from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.audit import UserProfileHistory, LeaveApplication
from association.app.forms.profile import ProfileChangeForm
from association.app.forms.department_change import DepartmentChangeForm
from association.app.utils.auth import get_current_user_optional, roles_required, minister_department_required

bp = Blueprint('profile_changes', __name__)

@bp.route('/me/change', methods=['GET', 'POST'])
@jwt_required()
def me_change():
    u = get_current_user_optional()
    form = ProfileChangeForm(obj=u)
    if request.method == 'POST' and form.validate_on_submit():
        changes = {}
        for field in ['name','class_name','gender','grade','phone','email']:
            new_val = form.data.get(field)
            if new_val and getattr(u, field) != new_val:
                changes[field] = {'old': getattr(u, field), 'new': new_val}
        if changes:
            hist = UserProfileHistory(user_id=u.id, changes=changes, status='pending', created_at=datetime.utcnow())
            db.session.add(hist)
            db.session.commit()
        return redirect(url_for('profile_changes.me_change'))
    return render_template('profile/me_change.html', form=form)

@bp.route('/admin/profile-changes', methods=['GET'])
@roles_required('president')
def admin_list():
    items = UserProfileHistory.query.filter_by(status='pending').order_by(UserProfileHistory.created_at.asc()).all()
    return render_template('profile/admin_list.html', items=items)

@bp.route('/admin/profile-changes/<int:hist_id>/approve', methods=['POST'])
@roles_required('president')
def admin_approve(hist_id):
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending':
        u = db.session.get(User, hist.user_id)
        for field, diff in hist.changes.items():
            setattr(u, field, diff['new'])
        u.updated_at = datetime.utcnow()
        hist.status = 'approved'
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.admin_list'))

@bp.route('/admin/profile-changes/<int:hist_id>/reject', methods=['POST'])
@roles_required('president')
def admin_reject(hist_id):
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending':
        hist.status = 'rejected'
        hist.reason = request.form.get('reason')
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.admin_list'))

@bp.route('/leader/profile-changes', methods=['GET'])
@minister_department_required()
def leader_list():
    u = get_current_user_optional()
    items = UserProfileHistory.query.join(User, UserProfileHistory.user_id == User.id).filter(User.department_id == u.department_id, UserProfileHistory.status=='pending').order_by(UserProfileHistory.created_at.asc()).all()
    return render_template('profile/leader_list.html', items=items)

@bp.route('/me/change-department', methods=['GET', 'POST'])
@jwt_required()
def me_change_department():
    u = get_current_user_optional()
    form = DepartmentChangeForm()
    deps = Department.query.order_by(Department.name.asc()).all()
    form.target_department_id.choices = [(d.id, d.name) for d in deps]
    if request.method == 'POST' and form.validate_on_submit():
        target = form.data['target_department_id']
        if u.department_id == target:
            return render_template('profile/me_change_department.html', form=form, error='目标部门与当前部门相同')
        changes = { 'department_id': { 'old': u.department_id, 'new': target } }
        hist = UserProfileHistory(user_id=u.id, changes=changes, status='pending', created_at=datetime.utcnow())
        db.session.add(hist)
        db.session.commit()
        return render_template('profile/me_change_department.html', form=form, success='已提交部门更换申请，待审批')
    return render_template('profile/me_change_department.html', form=form)

@bp.route('/me/leave', methods=['GET', 'POST'])
@jwt_required()
def me_leave():
    u = get_current_user_optional()
    if request.method == 'POST':
        reason = request.form.get('reason')
        la = LeaveApplication(user_id=u.id, reason=reason, status='pending', created_at=datetime.utcnow())
        db.session.add(la)
        db.session.commit()
        return render_template('profile/me_leave.html', success='退会申请已提交，待审核')
    return render_template('profile/me_leave.html')

@bp.route('/admin/department-changes', methods=['GET'])
@roles_required('president')
def admin_department_changes():
    items = UserProfileHistory.query.filter_by(status='pending').order_by(UserProfileHistory.created_at.asc()).all()
    items = [h for h in items if 'department_id' in (h.changes or {})]
    return render_template('profile/admin_department_changes.html', items=items)

@bp.route('/admin/department-changes/<int:hist_id>/approve', methods=['POST'])
@roles_required('president')
def admin_department_approve(hist_id):
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending' and 'department_id' in (hist.changes or {}):
        u = db.session.get(User, hist.user_id)
        new_dep = hist.changes['department_id']['new']
        u.department_id = new_dep
        u.updated_at = datetime.utcnow()
        hist.status = 'approved'
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.admin_department_changes'))

@bp.route('/admin/department-changes/<int:hist_id>/reject', methods=['POST'])
@roles_required('president')
def admin_department_reject(hist_id):
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending' and 'department_id' in (hist.changes or {}):
        hist.status = 'rejected'
        hist.reason = request.form.get('reason')
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.admin_department_changes'))

@bp.route('/leader/department-changes', methods=['GET'])
@minister_department_required()
def leader_department_changes():
    u = get_current_user_optional()
    items = UserProfileHistory.query.filter_by(status='pending').order_by(UserProfileHistory.created_at.asc()).all()
    # 目标部门为本部长所在部门才显示
    items = [h for h in items if 'department_id' in (h.changes or {}) and h.changes['department_id']['new'] == u.department_id]
    return render_template('profile/leader_department_changes.html', items=items)

@bp.route('/leader/department-changes/<int:hist_id>/approve', methods=['POST'])
@minister_department_required()
def leader_department_approve(hist_id):
    u = get_current_user_optional()
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending' and 'department_id' in (hist.changes or {}) and hist.changes['department_id']['new'] == u.department_id:
        target_user = db.session.get(User, hist.user_id)
        target_user.department_id = u.department_id
        target_user.updated_at = datetime.utcnow()
        hist.status = 'approved'
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.leader_department_changes'))

@bp.route('/leader/department-changes/<int:hist_id>/reject', methods=['POST'])
@minister_department_required()
def leader_department_reject(hist_id):
    u = get_current_user_optional()
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending' and 'department_id' in (hist.changes or {}) and hist.changes['department_id']['new'] == u.department_id:
        hist.status = 'rejected'
        hist.reason = request.form.get('reason')
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.leader_department_changes'))

@bp.route('/leader/profile-changes/<int:hist_id>/approve', methods=['POST'])
@minister_department_required()
def leader_approve(hist_id):
    u = get_current_user_optional()
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending':
        target = db.session.get(User, hist.user_id)
        if target.department_id != u.department_id:
            return redirect(url_for('profile_changes.leader_list'))
        for field, diff in hist.changes.items():
            setattr(target, field, diff['new'])
        target.updated_at = datetime.utcnow()
        hist.status = 'approved'
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.leader_list'))

@bp.route('/leader/profile-changes/<int:hist_id>/reject', methods=['POST'])
@minister_department_required()
def leader_reject(hist_id):
    u = current_user()
    hist = db.session.get(UserProfileHistory, hist_id)
    if hist and hist.status == 'pending':
        target = db.session.get(User, hist.user_id)
        if target.department_id != u.department_id:
            return redirect(url_for('profile_changes.leader_list'))
        hist.status = 'rejected'
        hist.reason = request.form.get('reason')
        hist.decided_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('profile_changes.leader_list'))
