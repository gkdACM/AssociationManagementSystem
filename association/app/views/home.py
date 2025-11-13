from flask import Blueprint, render_template, redirect, url_for
from association.app.extensions import db
from association.app.models.user import User, Department

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    return render_template('home.html')

@bp.route('/leaders')
def leaders():
    president = User.query.filter_by(role='president').first()
    vps = User.query.filter_by(role='vice_president').order_by(User.name.asc()).all()
    deps = Department.query.order_by(Department.name.asc()).all()
    ministers = {}
    for d in deps:
        m = User.query.filter_by(department_id=d.id, role='minister').order_by(User.updated_at.desc()).first()
        ministers[d.id] = m
    return render_template('public/leaders.html', president=president, vps=vps, deps=deps, ministers=ministers)
