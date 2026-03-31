# This file initializes Flask extensions (SQLAlchemy, Migrate, JWTManager).
# These extensions are then used in the `create_app` factory.
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()