from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.activity import Activity, ActivityApplication
from association.app.utils.auth import minister_department_required, get_current_user_optional
from association.app.models.points import PointsLedger

bp = Blueprint('leader_activities', __name__, url_prefix='/leader')

@bp.route('/activities', methods=['GET'])
@minister_department_required()
def activities():
    u = get_current_user_optional()
    items = Activity.query.filter_by(department_id=u.department_id).order_by(Activity.event_date.desc()).all()
    return render_template('leader/activities.html', items=items)

@bp.route('/activities/<int:act_id>/applications', methods=['GET','POST'])
@minister_department_required()
def applications(act_id):
    u = get_current_user_optional()
    a = db.session.get(Activity, act_id)
    if not a or a.department_id != u.department_id:
        return redirect(url_for('leader_activities.activities'))
    if request.method == 'POST':
        app_id = request.form.get('app_id', type=int)
        action = request.form.get('action')
        ap = db.session.get(ActivityApplication, app_id)
        if ap and ap.activity_id == a.id:
            if action == 'approve':
                ap.status = 'approved'
                ap.decided_at = datetime.utcnow()
            elif action == 'reject':
                ap.status = 'rejected'
                ap.decided_at = datetime.utcnow()
            db.session.commit()
        return redirect(url_for('leader_activities.applications', act_id=act_id))
    apps = ActivityApplication.query.filter_by(activity_id=a.id).order_by(ActivityApplication.applied_at.desc()).all()
    for ap in apps:
        ap.user = db.session.get(User, ap.user_id)
    return render_template('leader/activity_applications.html', activity=a, apps=apps)

@bp.route('/activities/<int:act_id>/penalties', methods=['GET','POST'])
@minister_department_required()
def penalties(act_id):
    u = get_current_user_optional()
    a = db.session.get(Activity, act_id)
    if not a or a.department_id != u.department_id:
        return redirect(url_for('leader_activities.activities'))
    apps = ActivityApplication.query.filter_by(activity_id=a.id, status='approved').order_by(ActivityApplication.applied_at.asc()).all()
    for ap in apps:
        ap.user = db.session.get(User, ap.user_id)
    if request.method == 'POST':
        cnt = 0
        for ap in apps:
            if request.form.get(f'absent_{ap.id}'):
                db.session.add(PointsLedger(user_id=ap.user_id, source_type='activity', source_id=a.id, points=-2, remark=f'活动[{a.name}]缺席扣分'))
                cnt += 1
            if request.form.get(f'failed_{ap.id}'):
                db.session.add(PointsLedger(user_id=ap.user_id, source_type='activity', source_id=a.id, points=-1, remark=f'活动[{a.name}]未达标扣分'))
                cnt += 1
        db.session.commit()
        return render_template('leader/activity_penalties.html', activity=a, apps=apps, success=f'已记录扣分 {cnt} 项')
    return render_template('leader/activity_penalties.html', activity=a, apps=apps)

@bp.route('/activities/<int:act_id>/applications/export', methods=['GET'])
@minister_department_required()
def export_applications(act_id):
    u = get_current_user_optional()
    a = db.session.get(Activity, act_id)
    if not a or a.department_id != u.department_id:
        return redirect(url_for('leader_activities.activities'))
    items = ActivityApplication.query.filter_by(activity_id=a.id, status='approved').order_by(ActivityApplication.applied_at.asc()).all()
    import io, csv
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['student_id','name','department','applied_at','decided_at'])
    for ap in items:
        u2 = db.session.get(User, ap.user_id)
        dep = u2.department.name if u2 and u2.department else ''
        w.writerow([u2.student_id if u2 else '', u2.name if u2 else '', dep, ap.applied_at, ap.decided_at])
    output.seek(0)
    from flask import send_file
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'activity_{act_id}_approved.csv')
