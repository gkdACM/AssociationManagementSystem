from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.project import Project, ProjectParticipation
from association.app.forms.project import ProjectForm, ParticipationDecisionForm
from association.app.utils.auth import minister_department_required, get_current_user_optional

bp = Blueprint('leader_projects', __name__, url_prefix='/leader')

@bp.route('/projects', methods=['GET', 'POST'])
@minister_department_required()
def projects():
    user = get_current_user_optional()
    form = ProjectForm()
    form.department_id.choices = [(user.department_id, Department.query.get(user.department_id).name)]
    if request.method == 'POST' and form.validate_on_submit():
        proj = Project(
            name=form.data['name'],
            description=form.data['description'],
            department_id=user.department_id,
            leader_user_id=user.id,
            github_url=form.data['github_url'],
            status='active',
            start_date=form.data['start_date'],
            end_date=form.data['end_date'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(proj)
        db.session.commit()
        return redirect(url_for('leader_projects.projects'))
    items = Project.query.filter_by(department_id=user.department_id).order_by(Project.created_at.desc()).all()
    return render_template('leader/projects.html', form=form, items=items)

@bp.route('/projects/<int:project_id>', methods=['GET', 'POST'])
@minister_department_required()
def edit_project(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if not proj or proj.department_id != user.department_id:
        return redirect(url_for('leader_projects.projects'))
    form = ProjectForm(obj=proj)
    form.department_id.choices = [(user.department_id, Department.query.get(user.department_id).name)]
    if request.method == 'POST' and form.validate_on_submit():
        proj.name = form.data['name']
        proj.description = form.data['description']
        proj.github_url = form.data['github_url']
        proj.start_date = form.data['start_date']
        proj.end_date = form.data['end_date']
        proj.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('leader_projects.projects'))
    return render_template('leader/project_form.html', form=form, proj=proj)

@bp.route('/projects/<int:project_id>/mark_complete', methods=['POST'])
@minister_department_required()
def mark_complete(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if proj and proj.department_id == user.department_id:
        proj.status = 'pending_acceptance'
        proj.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('leader_projects.projects'))

@bp.route('/projects/<int:project_id>/participants', methods=['GET', 'POST'])
@minister_department_required()
def participants(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if not proj or proj.department_id != user.department_id:
        return redirect(url_for('leader_projects.projects'))
    if request.method == 'POST':
        pid = request.form.get('pid', type=int)
        action = request.form.get('action')
        part = db.session.get(ProjectParticipation, pid)
        if part and part.project_id == proj.id:
            if action == 'approve':
                part.status = 'approved'
                part.decided_at = datetime.utcnow()
            elif action == 'reject':
                part.status = 'rejected'
                part.decided_at = datetime.utcnow()
            db.session.commit()
        return redirect(url_for('leader_projects.participants', project_id=project_id))
    parts = ProjectParticipation.query.filter_by(project_id=proj.id).order_by(ProjectParticipation.applied_at.desc()).all()
    return render_template('leader/project_participants.html', proj=proj, parts=parts)

@bp.route('/projects/acceptances', methods=['GET'])
@minister_department_required()
def acceptances():
    user = get_current_user_optional()
    items = Project.query.filter_by(department_id=user.department_id, status='pending_acceptance').order_by(Project.updated_at.desc()).all()
    return render_template('leader/project_acceptances.html', items=items)

@bp.route('/projects/<int:project_id>/accept', methods=['POST'])
@minister_department_required()
def accept(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if proj and proj.department_id == user.department_id:
        proj.status = 'accepted'
        proj.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('leader_projects.acceptances'))

@bp.route('/projects/<int:project_id>/reject', methods=['POST'])
@minister_department_required()
def reject(project_id):
    user = get_current_user_optional()
    proj = db.session.get(Project, project_id)
    if proj and proj.department_id == user.department_id:
        proj.status = 'rejected'
        proj.updated_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('leader_projects.acceptances'))

