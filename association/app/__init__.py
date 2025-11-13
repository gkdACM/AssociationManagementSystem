from flask import Flask
from association.config import Config
from association.app.extensions import db, migrate, jwt, csrf
from association.app.views.admin_competitions import bp as admin_competitions_bp
from association.app.views.leader_competitions import bp as leader_competitions_bp
from association.app.views.member_competitions import bp as member_competitions_bp
from association.app.views.leader_projects import bp as leader_projects_bp
from association.app.views.member_projects import bp as member_projects_bp
from association.app.views.admin_projects import bp as admin_projects_bp
from association.app.views.admin_activities import bp as admin_activities_bp
from association.app.views.leader_activities import bp as leader_activities_bp
from association.app.views.member_activities import bp as member_activities_bp
from association.app.views.dev import bp as dev_bp
from association.app.views.home import bp as home_bp
from association.app.views.auth import bp as auth_bp
from association.app.views.admin_users import bp as admin_users_bp
from association.app.views.admin_departments import bp as admin_departments_bp
from association.app.views.points import bp as points_bp
from association.app.views.setup import bp as setup_bp
from association.app.views.profile_changes import bp as profile_changes_bp
from association.app.utils.auth import get_current_user_optional
from flask import redirect, url_for, render_template

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    csrf.init_app(app)
    @jwt.unauthorized_loader
    def _unauthorized(reason):
        return render_template('errors/401.html', reason=reason), 401
    @jwt.invalid_token_loader
    def _invalid(reason):
        return render_template('errors/401.html', reason=reason), 401
    @jwt.expired_token_loader
    def _expired(jwt_header, jwt_payload):
        return render_template('errors/401.html', reason='登录已过期'), 401
    @jwt.needs_fresh_token_loader
    def _needs_fresh(jwt_header, jwt_payload):
        return render_template('errors/401.html', reason='需要重新登录'), 401
    @jwt.revoked_token_loader
    def _revoked(jwt_header, jwt_payload):
        return render_template('errors/401.html', reason='登录已失效'), 401
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_competitions_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_departments_bp)
    app.register_blueprint(leader_competitions_bp)
    app.register_blueprint(member_competitions_bp)
    app.register_blueprint(leader_projects_bp)
    app.register_blueprint(member_projects_bp)
    app.register_blueprint(admin_projects_bp)
    app.register_blueprint(admin_activities_bp)
    app.register_blueprint(leader_activities_bp)
    app.register_blueprint(member_activities_bp)
    app.register_blueprint(points_bp)
    app.register_blueprint(dev_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(profile_changes_bp)

    @app.context_processor
    def inject_user():
        u = get_current_user_optional()
        def role_cn(role, dep_name=None):
            if role == 'president':
                return '会长'
            if role == 'vice_president':
                return '副会长'
            if role == 'minister':
                return f"{dep_name or ''}部长".strip()
            return '成员'
        return dict(current_user=u, role_cn=role_cn)

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return render_template('errors/401.html', reason='未登录或会话无效'), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        return render_template('errors/403.html', reason='权限不足'), 403

    return app
