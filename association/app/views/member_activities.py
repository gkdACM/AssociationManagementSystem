from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User
from association.app.models.activity import Activity, ActivityApplication
from association.app.utils.auth import get_current_user_optional
from flask_jwt_extended import jwt_required

bp = Blueprint('member_activities', __name__)

@bp.route('/activities')
@jwt_required()
def activities():
    u = get_current_user_optional()
    items = Activity.query.filter((Activity.department_id == None) | (Activity.department_id == u.department_id)).order_by(Activity.event_date.asc()).all()
    return render_template('member/activities.html', items=items)

@bp.route('/activities/<int:act_id>/apply', methods=['POST'])
@jwt_required()
def apply(act_id):
    u = get_current_user_optional()
    a = db.session.get(Activity, act_id)
    if a:
        exists = ActivityApplication.query.filter_by(activity_id=a.id, user_id=u.id).first()
        if not exists:
            ap = ActivityApplication(activity_id=a.id, user_id=u.id, status='pending', applied_at=datetime.utcnow())
            db.session.add(ap)
            db.session.commit()
    return redirect(url_for('member_activities.activities'))

@bp.route('/my/activities')
@jwt_required()
def my_activities():
    u = get_current_user_optional()
    apps = ActivityApplication.query.filter_by(user_id=u.id).order_by(ActivityApplication.applied_at.desc()).all()
    for ap in apps:
        ap.activity = db.session.get(Activity, ap.activity_id)
    return render_template('member/my_activities.html', apps=apps)
