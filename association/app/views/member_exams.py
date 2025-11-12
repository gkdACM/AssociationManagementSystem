from datetime import date
from flask import Blueprint, render_template
from association.app.extensions import db
from association.app.models.exam import Exam, ExamResult
from association.app.utils.auth import get_current_user_optional
from flask_jwt_extended import jwt_required

bp = Blueprint('member_exams', __name__)

@bp.route('/exams')
@jwt_required()
def exams():
    verify_user = get_current_user_optional()
    user = verify_user
    items = Exam.query.filter((Exam.department_id == None) | (Exam.department_id == user.department_id)).order_by(Exam.exam_date.asc()).all()
    return render_template('member/exams.html', items=items)

@bp.route('/my/results')
@jwt_required()
def my_results():
    user = get_current_user_optional()
    results = ExamResult.query.filter_by(user_id=user.id).order_by(ExamResult.created_at.desc()).all()
    return render_template('member/my_results.html', results=results)
