# newZRL/__init__.py
import logging
import sys # Added import
from flask import Flask, jsonify, render_template, request # Added jsonify, render_template, request
# ... (other imports)
logger = logging.getLogger(__name__) # Define logger at module level
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flasgger import Flasgger
from flask_migrate import Migrate # Import Flask-Migrate
from flask_wtf.csrf import CSRFProtect # Import Flask-WTF CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix # Add for Render Proxy

# -----------------------------
# Inizializza estensioni
# -----------------------------
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
cors = CORS()
swagger = Flasgger()
migrate = Migrate() # Initialize Migrate extension
csrf = CSRFProtect() # Initialize CSRFProtect

# User loader per Flask-Login (ora definito al top-level)
from newZRL.models.user import User # Moved this import here
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models.season import Season
from newZRL.models.round import Round
from newZRL.models.race import Race
from newZRL.models.race_lineup import RaceLineup # Assuming RaceLineup is the class name
from newZRL.models.race_results import RaceResultsTeam, RaceResultsRider, RoundStanding
from newZRL.models.wtrl import WTRLLeague, WTRLDivision, WTRLCompetition, WTRLRace # Assuming these are class names
# Add other models as needed
@login_manager.user_loader
def load_user(user_id):
    """Callback per Flask-Login per caricare un utente dall'ID utente."""
    return User.query.get(int(user_id))

def create_app(config_name="development"):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Carica la configurazione corretta
    from .config import config_by_name
    app.config.from_object(config_by_name[config_name])

    # Ensure app.secret_key is set for session management
    app.secret_key = app.config.get("SECRET_KEY")
    if not app.secret_key:
        raise ValueError("Nessuna SECRET_KEY impostata per l'applicazione Flask o per la gestione della sessione.")
    logger.debug(f"App SECRET_KEY: {app.secret_key[:5]}...") # Log first 5 chars for security
    logger.debug(f"Session Cookie Name: {app.config.get('SESSION_COOKIE_NAME')}")
    logger.debug(f"Session Cookie Domain: {app.config.get('SESSION_COOKIE_DOMAIN')}")
    logger.debug(f"Session Cookie Samesite: {app.config.get('SESSION_COOKIE_SAMESITE')}")
    
    # Ensure WTF_CSRF_ENABLED is True for Flask-WTF CSRF protection
    app.config["WTF_CSRF_ENABLED"] = True

    # Controlla la SECRET_KEY per ambienti non di test
    if config_name != "testing" and not app.config.get("SECRET_KEY"):
        raise ValueError("Nessuna SECRET_KEY impostata per l'applicazione Flask")

    # Controlla l'URL del database per ambienti non di test
    if config_name in ["development", "production"] and not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise ValueError(f"Nessun SQLALCHEMY_DATABASE_URI impostato per l'ambiente {config_name}")

    # Imposta il logging
    # Ensure logging is sent to stdout for visibility in dev environment
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(app.config["LOGGING_LEVEL"])
    # Clear existing handlers to prevent duplicate output if basicConfig was called elsewhere
    if root_logger.handlers:
        for h in root_logger.handlers:
            root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    # Inizializza estensioni con l'app
    db.init_app(app)
    login_manager.init_app(app)
    cors.init_app(app)
    swagger.init_app(app)
    migrate.init_app(app, db) # Initialize Migrate with the app and db
    csrf.init_app(app) # Initialize CSRFProtect with the app

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Chiude la sessione del database al termine di ogni richiesta
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    # Custom CSRF Error Handler for AJAX requests
    from flask_wtf.csrf import CSRFError # Needs to be imported inside create_app to access app context if not at module level
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(f"CSRF Error: {e.description} for request {request.path}")
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({'status': 'error', 'message': e.description}), 400
        return render_template('400.html', message=e.description), 400

    # -----------------------------
    # HEALTH CHECK per Render
    # -----------------------------
    @app.route("/health")
    def health():
        return "ok", 200

    # -----------------------------
    # Blueprint
    # -----------------------------
    from newZRL.blueprints.auth.routes import auth_bp
    from newZRL.blueprints.main.routes import main_bp
    from newZRL.blueprints.api.routes import api_bp # Added api_bp
    from newZRL.blueprints.admin.bp import admin_bp
    from newZRL.blueprints.captain.routes import captain_bp # Import captain_bp
    from newZRL.blueprints.rider import rider_bp # Import rider_bp
    
    # Importare il pacchetto admin per eseguire il suo __init__.py e registrare le rotte
    import newZRL.blueprints.admin

    # -----------------------------
    # Registrazione blueprint
    # -----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp) # Registered api_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(captain_bp) # Register captain_bp
    app.register_blueprint(rider_bp) # Register rider_bp

    return app