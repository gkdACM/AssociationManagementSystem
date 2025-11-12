import io
import csv
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.exam import Exam, ExamResult
from association.app.models.points import PointsLedger
from association.app.forms.exam import ExamForm, ExamResultForm, ExamImportForm
from association.app.utils.auth import roles_required

bp = Blueprint('admin_exams', __name__, url_prefix='/admin')

@bp.route('/exams', methods=['GET', 'POST'])
@roles_required('president')
def exams():
    form = ExamForm()
    form.department_id.choices = [(0, '全协会')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        dep_id = form.data['department_id'] or 0
        exam = Exam(
            title=form.data['title'],
            description=form.data['description'],
            department_id=None if dep_id == 0 else dep_id,
            exam_date=form.data['exam_date'],
            pass_threshold=form.data['pass_threshold'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(exam)
        db.session.commit()
        return redirect(url_for('admin_exams.exams'))
    items = Exam.query.order_by(Exam.exam_date.desc()).all()
    return render_template('admin/exams.html', form=form, items=items)

@bp.route('/exams/<int:exam_id>', methods=['GET', 'POST'])
@roles_required('president')
def edit_exam(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return redirect(url_for('admin_exams.exams'))
    form = ExamForm(obj=exam)
    form.department_id.choices = [(0, '全协会')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        dep_id = form.data['department_id'] or 0
        exam.title = form.data['title']
        exam.description = form.data['description']
        exam.department_id = None if dep_id == 0 else dep_id
        exam.exam_date = form.data['exam_date']
        exam.pass_threshold = form.data['pass_threshold']
        exam.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('admin_exams.exams'))
    dep_choice = 0 if exam.department_id is None else exam.department_id
    form.department_id.data = dep_choice
    return render_template('admin/exam_form.html', form=form, exam=exam)

@bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@roles_required('president')
def delete_exam(exam_id):
    exam = db.session.get(Exam, exam_id)
    if exam:
        ExamResult.query.filter_by(exam_id=exam_id).delete()
        db.session.delete(exam)
        db.session.commit()
    return redirect(url_for('admin_exams.exams'))

@bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@roles_required('president')
def exam_results(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return redirect(url_for('admin_exams.exams'))
    form = ExamResultForm()
    import_form = ExamImportForm()
    if request.method == 'POST':
        if 'file' in request.files and import_form.validate_on_submit():
            f = request.files['file']
            data = f.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(data))
            created = 0
            updated = 0
            errors = 0
            for row in reader:
                sid = row.get('student_id')
                score_s = row.get('score')
                remark = row.get('remark')
                if not sid or score_s is None:
                    errors += 1
                    continue
                user = User.query.filter_by(student_id=sid).first()
                if not user:
                    errors += 1
                    continue
                score_val = float(score_s)
                passed = False
                if exam.pass_threshold is not None:
                    passed = score_val >= float(exam.pass_threshold)
                res = ExamResult.query.filter_by(exam_id=exam.id, user_id=user.id).first()
                if res:
                    res.score = score_val
                    res.passed = passed
                    res.remark = remark
                    res.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    res = ExamResult(
                        exam_id=exam.id,
                        user_id=user.id,
                        score=score_val,
                        passed=passed,
                        remark=remark,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.session.add(res)
                    created += 1
            db.session.commit()
            return redirect(url_for('admin_exams.exam_results', exam_id=exam_id))
        elif form.validate_on_submit():
            user = User.query.filter_by(student_id=form.data['student_id']).first()
            if not user:
                return redirect(url_for('admin_exams.exam_results', exam_id=exam_id))
            score_val = float(form.data['score'])
            passed = False
            if exam.pass_threshold is not None:
                passed = score_val >= float(exam.pass_threshold)
            res = ExamResult.query.filter_by(exam_id=exam.id, user_id=user.id).first()
            if res:
                res.score = score_val
                res.passed = passed
                res.remark = form.data['remark']
                res.updated_at = datetime.utcnow()
            else:
                res = ExamResult(
                    exam_id=exam.id,
                    user_id=user.id,
                    score=score_val,
                    passed=passed,
                    remark=form.data['remark'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.session.add(res)
            db.session.commit()
            pts = int(score_val)
            db.session.add(PointsLedger(user_id=user.id, source_type='exam', source_id=exam.id, points=pts, remark='考试积分', created_at=datetime.utcnow()))
            db.session.commit()
            return redirect(url_for('admin_exams.exam_results', exam_id=exam_id))
    results = ExamResult.query.filter_by(exam_id=exam.id).order_by(ExamResult.score.desc()).all()
    return render_template('admin/exam_results.html', exam=exam, results=results, form=form, import_form=import_form)

@bp.route('/exams/<int:exam_id>/results/export', methods=['GET'])
@roles_required('president')
def export_results(exam_id):
    exam = db.session.get(Exam, exam_id)
    if not exam:
        return redirect(url_for('admin_exams.exams'))
    results = ExamResult.query.filter_by(exam_id=exam.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['student_id', 'name', 'score', 'passed', 'remark'])
    for r in results:
        u = db.session.get(User, r.user_id)
        writer.writerow([u.student_id if u else '', u.name if u else '', float(r.score), 1 if r.passed else 0, r.remark or ''])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'exam_{exam_id}_results.csv')
