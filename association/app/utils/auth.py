from flask import abort, session
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from association.app.extensions import db
from association.app.models.user import User

def get_current_user_optional():
    uid = None
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
    except Exception:
        pass
    if not uid:
        uid = session.get('uid')
    return db.session.get(User, uid) if uid else None

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            uid = session.get('uid')
            if not uid:
                try:
                    verify_jwt_in_request(optional=True)
                    uid = get_jwt_identity()
                except Exception:
                    uid = None
            if not uid:
                abort(401)
            user = db.session.get(User, uid)
            if not user or user.role not in roles or user.registration_status != 'approved' or not user.is_active:
                abort(403)
            return fn(*args, **kwargs)
        return inner
    return wrapper

def minister_department_required():
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            uid = session.get('uid')
            if not uid:
                try:
                    verify_jwt_in_request(optional=True)
                    uid = get_jwt_identity()
                except Exception:
                    uid = None
            if not uid:
                abort(401)
            user = db.session.get(User, uid)
            if not user or user.role != 'minister' or not user.department_id or user.registration_status != 'approved' or not user.is_active:
                abort(403)
            return fn(*args, **kwargs)
        return inner
    return wrapper
