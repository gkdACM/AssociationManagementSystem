from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
csrf = CSRFProtect()
