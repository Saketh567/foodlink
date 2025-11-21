from datetime import datetime
from flask import Flask, render_template, session
from .config import Config
from .database import init_db
from app.utils.helpers import query_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DB pool
    init_db(app)

    # BLUEPRINTS
    from app.routes.auth_routes import auth_bp
    from app.routes.address_routes import address_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.client_routes import client_bp
    from app.routes.volunteer_routes import volunteer_bp
    from app.routes.notification_routes import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(address_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(notifications_bp)

    @app.context_processor
    def inject_globals():
        unread_notifications = 0
        user_id = session.get("user_id")
        if user_id:
            unread_notifications = query_db(
                "SELECT COUNT(*) AS c FROM notifications WHERE user_id=%s AND is_read=0",
                (user_id,),
                one=True,
            )["c"]
        return {
            "current_year": datetime.utcnow().year,
            "unread_notifications": unread_notifications,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
