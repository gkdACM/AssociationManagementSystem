from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, send_file
import io, csv
from flask_jwt_extended import jwt_required
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.audit import UserProfileHistory, LeaveApplication
from association.app.forms.profile import ProfileChangeForm
from association.app.forms.department_change import DepartmentChangeForm
from association.app.utils.auth import get_current_user_optional, roles_required, minister_department_required
from association.app.models.competition import CompetitionResult, Competition
from association.app.models.project import ProjectParticipation, Project
from association.app.views.auth import hash_password

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

@bp.route('/me/profile', methods=['GET'])
@jwt_required()
def me_profile():
    u = get_current_user_optional()
    comps = db.session.query(CompetitionResult).filter(CompetitionResult.user_id == u.id).order_by(CompetitionResult.created_at.desc()).all()
    for r in comps:
        r.competition = db.session.get(Competition, r.competition_id)
    parts = db.session.query(ProjectParticipation).filter(ProjectParticipation.user_id == u.id).order_by(ProjectParticipation.applied_at.desc()).all()
    for p in parts:
        p.project = db.session.get(Project, p.project_id)
    internal_awards = [r for r in comps if r.competition and r.competition.category == 'internal']
    external_awards = [r for r in comps if r.competition and r.competition.category == 'external']
    return render_template('profile/me_profile.html', user=u, internal_awards=internal_awards, external_awards=external_awards, parts=parts)

@bp.route('/me/honors/export', methods=['GET'])
@jwt_required()
def me_honors_export():
    u = get_current_user_optional()
    results = db.session.query(CompetitionResult).filter(CompetitionResult.user_id == u.id).order_by(CompetitionResult.created_at.asc()).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['类别','竞赛名称','等级','日期','部门','奖项','分数','备注'])
    for r in results:
        c = db.session.get(Competition, r.competition_id)
        if not c:
            continue
        cat_cn = '内部赛' if c.category == 'internal' else '外部赛'
        dep_name = c.department.name if c.department else ''
        w.writerow([cat_cn, c.name, c.level, c.event_date, dep_name, r.award or '', r.score or '', r.remark or ''])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='my_honors.csv')

@bp.route('/leader/reset-password', methods=['GET','POST'])
@minister_department_required()
def leader_reset_password():
    u = get_current_user_optional()
    if request.method == 'POST':
        sid = (request.form.get('student_id') or '').strip()
        target = User.query.filter_by(student_id=sid).first()
        if target and target.department_id == u.department_id and target.role not in ('president','vice_president','minister'):
            target.password_hash = hash_password('123456')
            target.updated_at = datetime.utcnow()
            db.session.commit()
            return render_template('leader/reset_password.html', success='已重置为 123456，登录后需修改密码')
        return render_template('leader/reset_password.html', error='学号不存在或不属于本部门，或不可重置')
    return render_template('leader/reset_password.html')

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
    u = get_current_user_optional()
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
