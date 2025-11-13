from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.competition import Competition, CompetitionResult
from association.app.forms.competition import CompetitionForm, CompetitionResultForm
from association.app.utils.auth import minister_department_required, get_current_user_optional

bp = Blueprint('leader_competitions', __name__, url_prefix='/leader')

@bp.route('/competitions', methods=['GET', 'POST'])
@minister_department_required()
def competitions():
    user = get_current_user_optional()
    form = CompetitionForm()
    form.department_id.choices = [(user.department_id, Department.query.get(user.department_id).name)]
    if request.method == 'POST' and form.validate_on_submit():
        comp = Competition(
            name=form.data['name'],
            description=form.data['description'],
            category=form.data['category'],
            level=form.data['level'],
            department_id=user.department_id,
            event_date=form.data['event_date'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        return redirect(url_for('leader_competitions.competitions'))
    items = Competition.query.filter_by(department_id=user.department_id).order_by(Competition.event_date.desc()).all()
    return render_template('admin/competitions.html', form=form, items=items)

@bp.route('/competitions/<int:comp_id>/results', methods=['GET', 'POST'])
@minister_department_required()
def competition_results(comp_id):
    user = get_current_user_optional()
    comp = db.session.get(Competition, comp_id)
    if not comp or comp.department_id != user.department_id:
        return redirect(url_for('leader_competitions.competitions'))
    form = CompetitionResultForm()
    if request.method == 'POST' and form.validate_on_submit():
        member = User.query.filter_by(student_id=form.data['student_id'], department_id=user.department_id).first()
        if not member:
            return redirect(url_for('leader_competitions.competition_results', comp_id=comp_id))
        score_val = float(form.data['score']) if form.data['score'] is not None else None
        res = CompetitionResult.query.filter_by(competition_id=comp.id, user_id=member.id).first()
        if res:
            res.score = score_val
            res.award = form.data['award']
            res.remark = form.data['remark']
            res.updated_at = datetime.utcnow()
        else:
            res = CompetitionResult(
                competition_id=comp.id,
                user_id=member.id,
                score=score_val,
                award=form.data['award'],
                remark=form.data['remark'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(res)
        db.session.commit()
        return redirect(url_for('leader_competitions.competition_results', comp_id=comp_id))
    results = CompetitionResult.query.filter_by(competition_id=comp.id).order_by(CompetitionResult.created_at.desc()).all()
    return render_template('admin/competition_results.html', comp=comp, results=results, form=form, import_form=None)

