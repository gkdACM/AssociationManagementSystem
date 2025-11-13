from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.project import Project
from association.app.models.user import User, Department
from association.app.utils.auth import roles_required
from association.app.forms.project import ProjectForm
from datetime import datetime

bp = Blueprint('admin_projects', __name__, url_prefix='/admin')

@bp.route('/projects', methods=['GET','POST'])
@roles_required('president', 'vice_president')
def projects():
    state = request.args.get('state', 'all')
    # creation form for president/vice_president
    form = ProjectForm()
    form.department_id.choices = [(0, '不指定')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        # current user creates project, leader specified by student_id
        dep_id = form.data['department_id'] or 0
        leader = User.query.filter_by(student_id=form.data['leader_student_id']).first()
        if not leader:
            return render_template('admin/projects.html', items=[], state=state, form=form, error='负责人学号不存在')
        proj = Project(
            name=form.data['name'],
            description=form.data['description'],
            department_id=None if dep_id == 0 else dep_id,
            leader_user_id=leader.id,
            github_url=form.data['github_url'],
            status='active',
            start_date=form.data['start_date'],
            end_date=None,
            created_at=date.today(),
            updated_at=date.today(),
        )
        db.session.add(proj)
        db.session.commit()
        return redirect(url_for('admin_projects.projects', state=state))
    q = Project.query
    today = date.today()
    if state == 'ongoing':
        q = q.filter(
            (Project.status.in_(['active', 'pending_acceptance'])) |
            (Project.end_date == None) |
            (Project.end_date >= today)
        )
    elif state == 'ended':
        q = q.filter(
            (Project.status.in_(['accepted', 'rejected'])) |
            (Project.end_date != None) & (Project.end_date < today)
        )
    items = q.order_by(Project.created_at.desc()).all()
    # eager load relations for template convenience
    for p in items:
        p.leader = db.session.get(User, p.leader_user_id)
        p.department = db.session.get(Department, p.department_id) if p.department_id else None
    return render_template('admin/projects.html', items=items, state=state, form=form)

@bp.route('/projects/<int:project_id>/submit', methods=['POST'])
@roles_required('president', 'vice_president')
def submit_project(project_id):
    # 项目负责人提交后进入待验收，由会长或副会长审核
    proj = db.session.get(Project, project_id)
    if proj and proj.status == 'active':
        proj.status = 'pending_acceptance'
        proj.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('admin_projects.projects'))

@bp.route('/projects/<int:project_id>/audit', methods=['POST'])
@roles_required('president', 'vice_president')
def audit_project(project_id):
    action = request.form.get('action')
    proj = db.session.get(Project, project_id)
    if proj and proj.status == 'pending_acceptance':
        if action == 'approve':
            proj.status = 'accepted'
            proj.end_date = date.today()
        else:
            proj.status = 'rejected'
        proj.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('admin_projects.projects'))
