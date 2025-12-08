# newZRL/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# -----------------------------
# Inizializza estensioni
# -----------------------------
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object("newZRL.config.Config")

    # Inizializza estensioni con l'app
    db.init_app(app)
    login_manager.init_app(app)

    # -----------------------------
    # HEALTH CHECK per Render
    # -----------------------------
    @app.route("/health")
    def health():
        return "ok", 200

    # -----------------------------
    # User loader
    # -----------------------------
    from newZRL.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -----------------------------
    # Blueprint reali
    # -----------------------------
    from newZRL.blueprints.auth.routes import auth_bp
    from newZRL.blueprints.main.routes import main_bp

    from newZRL.blueprints.admin.bp import admin_bp
    from newZRL.blueprints.admin import dashboard
    from newZRL.blueprints.admin.reports import admin_reports_bp
    from newZRL.blueprints.admin.export import admin_export_bp
    from newZRL.blueprints.admin.import_zwiftpower import import_zwift_bp
    from newZRL.blueprints.admin.wtrl_teams_import import wtrl_import_bp
    from newZRL.blueprints.admin.routes_import import bp_import
    from newZRL.blueprints.admin.import_wtrl_season import import_wtrl_season_bp
    from newZRL.blueprints.admin.race_importer import admin_race_bp  

    # -----------------------------
    # Registrazione blueprint
    # -----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(admin_reports_bp, url_prefix="/admin/reports")
    app.register_blueprint(admin_export_bp, url_prefix="/admin/reports/export")
    app.register_blueprint(import_zwift_bp, url_prefix="/admin/import_zwift")
    app.register_blueprint(wtrl_import_bp)
    app.register_blueprint(bp_import)
    app.register_blueprint(import_wtrl_season_bp, url_prefix='/admin/import_wtrl_season')
    app.register_blueprint(admin_race_bp, url_prefix='/admin/race')
    
    return app
