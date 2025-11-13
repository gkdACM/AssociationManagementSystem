import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.competition import Competition, CompetitionResult
from association.app.forms.competition import CompetitionForm, CompetitionResultForm, CompetitionImportForm
from association.app.utils.auth import roles_required

bp = Blueprint('admin_competitions', __name__, url_prefix='/admin')

@bp.route('/competitions', methods=['GET', 'POST'])
@roles_required('president', 'vice_president')
def competitions():
    form = CompetitionForm()
    form.department_id.choices = [(0, '不指定')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        dep_id = form.data['department_id'] or 0
        comp = Competition(
            name=form.data['name'],
            description=form.data['description'],
            category=form.data['category'],
            level=form.data['level'],
            department_id=None if dep_id == 0 else dep_id,
            event_date=form.data['event_date'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(comp)
        db.session.commit()
        return redirect(url_for('admin_competitions.competitions'))
    items = Competition.query.order_by(Competition.event_date.desc()).all()
    return render_template('admin/competitions.html', form=form, items=items)

@bp.route('/competitions/<int:comp_id>', methods=['GET', 'POST'])
@roles_required('president', 'vice_president')
def edit_competition(comp_id):
    comp = db.session.get(Competition, comp_id)
    if not comp:
        return redirect(url_for('admin_competitions.competitions'))
    form = CompetitionForm(obj=comp)
    form.department_id.choices = [(0, '不指定')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        dep_id = form.data['department_id'] or 0
        comp.name = form.data['name']
        comp.description = form.data['description']
        comp.category = form.data['category']
        comp.level = form.data['level']
        comp.department_id = None if dep_id == 0 else dep_id
        comp.event_date = form.data['event_date']
        comp.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin_competitions.competitions'))
    form.department_id.data = 0 if comp.department_id is None else comp.department_id
    return render_template('admin/competition_form.html', form=form, comp=comp)

@bp.route('/competitions/<int:comp_id>/delete', methods=['POST'])
@roles_required('president', 'vice_president')
def delete_competition(comp_id):
    comp = db.session.get(Competition, comp_id)
    if comp:
        CompetitionResult.query.filter_by(competition_id=comp_id).delete()
        db.session.delete(comp)
        db.session.commit()
    return redirect(url_for('admin_competitions.competitions'))

@bp.route('/competitions/<int:comp_id>/results', methods=['GET', 'POST'])
@roles_required('president', 'vice_president')
def competition_results(comp_id):
    comp = db.session.get(Competition, comp_id)
    if not comp:
        return redirect(url_for('admin_competitions.competitions'))
    form = CompetitionResultForm()
    import_form = CompetitionImportForm()
    if request.method == 'POST':
        if 'file' in request.files and import_form.validate_on_submit():
            f = request.files['file']
            data = f.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(data))
            for row in reader:
                sid = row.get('student_id')
                user = User.query.filter_by(student_id=sid).first()
                if not user:
                    continue
                score_s = row.get('score')
                award = row.get('award')
                score_val = float(score_s) if score_s else None
                res = CompetitionResult.query.filter_by(competition_id=comp.id, user_id=user.id).first()
                if res:
                    res.score = score_val
                    res.award = award
                    res.remark = row.get('remark')
                    res.updated_at = datetime.utcnow()
                else:
                    res = CompetitionResult(
                        competition_id=comp.id,
                        user_id=user.id,
                        score=score_val,
                        award=award,
                        remark=row.get('remark'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.session.add(res)
            db.session.commit()
            return redirect(url_for('admin_competitions.competition_results', comp_id=comp_id))
        elif form.validate_on_submit():
            user = User.query.filter_by(student_id=form.data['student_id']).first()
            if not user:
                return redirect(url_for('admin_competitions.competition_results', comp_id=comp_id))
            score_val = float(form.data['score']) if form.data['score'] is not None else None
            res = CompetitionResult.query.filter_by(competition_id=comp.id, user_id=user.id).first()
            if res:
                res.score = score_val
                res.award = form.data['award']
                res.remark = form.data['remark']
                res.updated_at = datetime.utcnow()
            else:
                res = CompetitionResult(
                    competition_id=comp.id,
                    user_id=user.id,
                    score=score_val,
                    award=form.data['award'],
                    remark=form.data['remark'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(res)
            db.session.commit()
            return redirect(url_for('admin_competitions.competition_results', comp_id=comp_id))
    results = CompetitionResult.query.filter_by(competition_id=comp.id).order_by(CompetitionResult.created_at.desc()).all()
    return render_template('admin/competition_results.html', comp=comp, results=results, form=form, import_form=import_form)

@bp.route('/competitions/<int:comp_id>/results/export', methods=['GET'])
@roles_required('president', 'vice_president')
def export_competition_results(comp_id):
    comp = db.session.get(Competition, comp_id)
    if not comp:
        return redirect(url_for('admin_competitions.competitions'))
    results = CompetitionResult.query.filter_by(competition_id=comp.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['student_id', 'name', 'score', 'award', 'remark'])
    for r in results:
        u = db.session.get(User, r.user_id)
        writer.writerow([u.student_id if u else '', u.name if u else '', float(r.score) if r.score is not None else '', r.award or '', r.remark or ''])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'competition_{comp_id}_results.csv')
