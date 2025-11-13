from flask import Blueprint, render_template, request
from association.app.utils.auth import roles_required, get_current_user_optional
from association.app.models.points import PointsLedger, Level
from association.app.models.user import User, Department
from flask_jwt_extended import jwt_required
from association.app.extensions import db

bp = Blueprint('points', __name__)

@bp.route('/levels')
def levels():
    items = Level.query.order_by(Level.threshold_points.asc()).all()
    return render_template('points/levels.html', items=items)

@bp.route('/my/points')
@jwt_required()
def my_points():
    u = get_current_user_optional()
    items = PointsLedger.query.filter_by(user_id=u.id).order_by(PointsLedger.created_at.desc()).all()
    total = sum(p.points for p in items)
    levels = Level.query.order_by(Level.threshold_points.asc()).all()
    current_level = None
    for lvl in levels:
        if total >= lvl.threshold_points:
            current_level = lvl
    return render_template('points/my_points.html', items=items, total=total, current_level=current_level)

@bp.route('/admin/points')
@roles_required('president','vice_president')
def admin_points():
    grade = request.args.get('grade')
    q = User.query
    if grade:
        q = q.filter(User.grade == grade)
    users = q.order_by(User.created_at.desc()).all()
    totals = {}
    for u in users:
        pts = sum(p.points for p in PointsLedger.query.filter_by(user_id=u.id).all())
        totals[u.id] = pts
    grades = [g[0] for g in db.session.query(User.grade).distinct().all()]
    return render_template('points/admin_points.html', users=users, totals=totals, grades=grades, current_grade=grade)
