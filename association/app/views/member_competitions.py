from flask import Blueprint, render_template
from association.app.extensions import db
from association.app.models.competition import Competition, CompetitionResult
from association.app.utils.auth import get_current_user_optional
from flask_jwt_extended import jwt_required

bp = Blueprint('member_competitions', __name__)

@bp.route('/competitions')
@jwt_required()
def competitions():
    user = get_current_user_optional()
    items = Competition.query.filter((Competition.category == 'external') | (Competition.department_id == user.department_id) | (Competition.department_id == None)).order_by(Competition.event_date.asc()).all()
    return render_template('member/competitions.html', items=items)

@bp.route('/my/competitions')
@jwt_required()
def my_competitions():
    user = get_current_user_optional()
    results = CompetitionResult.query.filter_by(user_id=user.id).order_by(CompetitionResult.created_at.desc()).all()
    return render_template('member/my_competitions.html', results=results)

