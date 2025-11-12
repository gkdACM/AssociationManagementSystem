from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.exam import Exam, ExamResult
from association.app.forms.exam import ExamForm, ExamResultForm
from association.app.utils.auth import minister_department_required, get_current_user_optional

bp = Blueprint('leader_exams', __name__, url_prefix='/leader')

@bp.route('/exams', methods=['GET', 'POST'])
@minister_department_required()
def exams():
    user = get_current_user_optional()
    form = ExamForm()
    form.department_id.choices = [(user.department_id, Department.query.get(user.department_id).name)]
    if request.method == 'POST' and form.validate_on_submit():
        exam = Exam(
            title=form.data['title'],
            description=form.data['description'],
            department_id=user.department_id,
            exam_date=form.data['exam_date'],
            pass_threshold=form.data['pass_threshold'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(exam)
        db.session.commit()
        return redirect(url_for('leader_exams.exams'))
    items = Exam.query.filter_by(department_id=user.department_id).order_by(Exam.exam_date.desc()).all()
    return render_template('admin/exams.html', form=form, items=items)

@bp.route('/exams/<int:exam_id>/results', methods=['GET', 'POST'])
@minister_department_required()
def exam_results(exam_id):
    user = get_current_user_optional()
    exam = db.session.get(Exam, exam_id)
    if not exam or exam.department_id != user.department_id:
        return redirect(url_for('leader_exams.exams'))
    form = ExamResultForm()
    if request.method == 'POST' and form.validate_on_submit():
        member = User.query.filter_by(student_id=form.data['student_id'], department_id=user.department_id).first()
        if not member:
            return redirect(url_for('leader_exams.exam_results', exam_id=exam_id))
        score_val = float(form.data['score'])
        passed = False
        if exam.pass_threshold is not None:
            passed = score_val >= float(exam.pass_threshold)
        res = ExamResult.query.filter_by(exam_id=exam.id, user_id=member.id).first()
        if res:
            res.score = score_val
            res.passed = passed
            res.remark = form.data['remark']
            res.updated_at = datetime.utcnow()
        else:
            res = ExamResult(
                exam_id=exam.id,
                user_id=member.id,
                score=score_val,
                passed=passed,
                remark=form.data['remark'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(res)
        db.session.commit()
        return redirect(url_for('leader_exams.exam_results', exam_id=exam_id))
    results = ExamResult.query.filter_by(exam_id=exam.id).order_by(ExamResult.score.desc()).all()
    return render_template('admin/exam_results.html', exam=exam, results=results, form=form, import_form=None)
