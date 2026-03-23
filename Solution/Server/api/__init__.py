from flask import Flask
from api.config import Config
from api.extensions import db, migrate, jwt
from api.routes import *
from flask_cors import CORS
from api.commands import fresh, seed, clear_uploads

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(marking_bp, url_prefix="/marking")
    app.register_blueprint(uploads_bp, url_prefix="/uploads")

    app.cli.add_command(fresh)
    app.cli.add_command(seed)
    app.cli.add_command(clear_uploads)

    allowed_origins = [
        "http://localhost:3000",  
    ]

    CORS(
        app,
        resources={
            r"/*": { # Apply CORS to all API routes
                "origins": allowed_origins
            }
        },
        supports_credentials=True, # VERY IMPORTANT: Allows cookies and Authorization headers
        allow_headers=["Content-Type", "Authorization"], # Explicitly allow these headers
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"] # Allow these methods
    )

    return app