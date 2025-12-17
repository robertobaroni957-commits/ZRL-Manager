# run_migrations.py
import os
import logging
from flask_migrate import upgrade
from newZRL import create_app, db

# Setup basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info("Starting database migration script...")

try:
    # Create an application instance
    # We must ensure FLASK_CONFIG is set; Render sets it to 'production' via render.yaml
    config_name = os.getenv("FLASK_CONFIG", "production")
    app = create_app(config_name)
    log.info(f"Flask app created with '{config_name}' configuration.")

    # Run the database migrations within the application context
    with app.app_context():
        log.info("Entering application context to run migrations.")
        
        # The PROD_DATABASE_URL should be available here as it's set in the environment
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            log.error("SQLALCHEMY_DATABASE_URI is not set. Cannot run migrations.")
            raise RuntimeError("Database URI not found.")
            
        log.info("SQLALCHEMY_DATABASE_URI is present.")
        
        log.info("Applying database migrations with 'upgrade'...")
        # The upgrade command from Flask-Migrate applies all pending migrations
        upgrade()
        log.info("Database migrations applied successfully.")

except Exception as e:
    log.error(f"An error occurred during migrations: {e}", exc_info=True)
    # Exit with a non-zero status code to halt the deployment on Render
    exit(1)

log.info("Migration script finished successfully.")
