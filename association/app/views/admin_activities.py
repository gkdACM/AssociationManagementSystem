from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department
from association.app.models.activity import Activity, ActivityApplication
from association.app.forms.activity import ActivityForm
from association.app.utils.auth import roles_required

bp = Blueprint('admin_activities', __name__, url_prefix='/admin')

@bp.route('/activities', methods=['GET','POST'])
@roles_required('president','vice_president')
def activities():
    form = ActivityForm()
    form.department_id.choices = [(0, '不指定')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
    if request.method == 'POST' and form.validate_on_submit():
        dep_id = form.data['department_id'] or 0
        a = Activity(
            name=form.data['name'],
            description=form.data['description'],
            department_id=None if dep_id == 0 else dep_id,
            event_date=form.data['event_date'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(a)
        db.session.commit()
        return redirect(url_for('admin_activities.activities'))
    items = Activity.query.order_by(Activity.event_date.desc()).all()
    return render_template('admin/activities.html', form=form, items=items)

@bp.route('/activities/<int:act_id>/applications', methods=['GET'])
@roles_required('president','vice_president')
def applications(act_id):
    a = db.session.get(Activity, act_id)
    if not a:
        return redirect(url_for('admin_activities.activities'))
    apps = ActivityApplication.query.filter_by(activity_id=a.id).order_by(ActivityApplication.applied_at.desc()).all()
    for ap in apps:
        ap.user = db.session.get(User, ap.user_id)
    return render_template('admin/activity_applications.html', activity=a, apps=apps)

@bp.route('/activities/<int:act_id>/applications/export', methods=['GET'])
@roles_required('president','vice_president')
def export_applications(act_id):
    a = db.session.get(Activity, act_id)
    if not a:
        return redirect(url_for('admin_activities.activities'))
    items = ActivityApplication.query.filter_by(activity_id=a.id, status='approved').order_by(ActivityApplication.applied_at.asc()).all()
    import io, csv
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['student_id','name','department','applied_at','decided_at'])
    for ap in items:
        u = db.session.get(User, ap.user_id)
        dep = u.department.name if u and u.department else ''
        w.writerow([u.student_id if u else '', u.name if u else '', dep, ap.applied_at, ap.decided_at])
    output.seek(0)
    from flask import send_file
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name=f'activity_{act_id}_approved.csv')
