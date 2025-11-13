from datetime import date
from flask import Blueprint, render_template, request
from association.app.extensions import db
from association.app.models.project import Project
from association.app.models.user import User, Department
from association.app.utils.auth import roles_required

bp = Blueprint('admin_projects', __name__, url_prefix='/admin')

@bp.route('/projects', methods=['GET'])
@roles_required('president', 'vice_president')
def projects():
    state = request.args.get('state', 'all')
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
    return render_template('admin/projects.html', items=items, state=state)

