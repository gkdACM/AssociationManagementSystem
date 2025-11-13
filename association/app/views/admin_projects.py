from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.project import Project
from association.app.models.user import User, Department
from association.app.utils.auth import roles_required
from association.app.forms.project import ProjectForm

bp = Blueprint('admin_projects', __name__, url_prefix='/admin')

@bp.route('/projects', methods=['GET','POST'])
@roles_required('president', 'vice_president')
def projects():
    state = request.args.get('state', 'all')
    # creation form for president/vice_president
    form = ProjectForm()
    form.department_id.choices = [(0, '不指定')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        # current user creates project, optional department
        from association.app.utils.auth import get_current_user_optional
        u = get_current_user_optional()
        dep_id = form.data['department_id'] or 0
        proj = Project(
            name=form.data['name'],
            description=form.data['description'],
            department_id=None if dep_id == 0 else dep_id,
            leader_user_id=u.id,
            github_url=form.data['github_url'],
            status='active',
            start_date=form.data['start_date'],
            end_date=form.data['end_date'],
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
