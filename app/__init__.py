"""
Flask Application Factory
Initializes the Flask app with all configurations, blueprints, and extensions
"""
from flask import Flask
from dotenv import load_dotenv
from app.config import Config

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # -----------------------------
    # Database (SQLite)
    # -----------------------------
    from app.database import init_db, close_db
    init_db(app)
    app.teardown_appcontext(close_db)

    # -----------------------------
    # Blueprints (Routes)
    # -----------------------------
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.volunteer_routes import volunteer_bp
    from app.routes.client_routes import client_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(volunteer_bp, url_prefix='/volunteer')
    app.register_blueprint(client_bp, url_prefix='/client')

    # -----------------------------
    # Index route
    # -----------------------------
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    return app
