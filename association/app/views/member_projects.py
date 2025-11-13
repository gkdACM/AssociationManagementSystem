from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.project import Project, ProjectParticipation
from association.app.utils.auth import get_current_user_optional
from flask_jwt_extended import jwt_required

bp = Blueprint('member_projects', __name__)

@bp.route('/projects')
@jwt_required()
def projects():
    user = get_current_user_optional()
    items = Project.query.filter(Project.status.in_(['active','pending_acceptance','accepted'])).order_by(Project.created_at.desc()).all()
    parts = {p.project_id: p for p in ProjectParticipation.query.filter_by(user_id=user.id).all()}
    return render_template('member/projects.html', items=items, parts=parts)

@bp.route('/projects/<int:project_id>/apply', methods=['POST'])
@jwt_required()
def apply(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if proj:
        exists = ProjectParticipation.query.filter_by(project_id=project_id, user_id=user.id).first()
        if not exists:
            part = ProjectParticipation(project_id=project_id, user_id=user.id, status='pending', applied_at=datetime.utcnow())
            db.session.add(part)
            db.session.commit()
    return redirect(url_for('member_projects.projects'))

@bp.route('/my/projects')
@jwt_required()
def my_projects():
    user = get_current_user_optional()
    parts = ProjectParticipation.query.filter_by(user_id=user.id).order_by(ProjectParticipation.applied_at.desc()).all()
    return render_template('member/my_projects.html', parts=parts)

