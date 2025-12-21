 # run_migrations.py
import os
import logging
from flask_migrate import upgrade
from newZRL import create_app
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info("Starting database migration script...")

try:
    config_name = os.getenv("FLASK_CONFIG", "production")
    app = create_app(config_name)
    log.info(f"Flask app created with '{config_name}' configuration.")

    with app.app_context():
        log.info("Entering application context to run migrations.")
        
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            log.error("SQLALCHEMY_DATABASE_URI is not set. Cannot run migrations.")
            raise RuntimeError("Database URI not found.")
            
        log.info("SQLALCHEMY_DATABASE_URI is present.")

        # Force drop alembic_version table to ensure migrations run on a 'clean' slate
        log.info("Attempting to drop alembic_version table to force re-migration...")
        try:
            from newZRL import db
            from sqlalchemy import text
            with db.engine.connect() as connection:
                connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
                log.info("Successfully dropped alembic_version table (if it existed).")
        except Exception as e:
            log.warning(f"Could not drop alembic_version table, continuing anyway. Error: {e}")

        log.info("Applying database migrations with 'upgrade'...")
        
        upgrade() 
        
        log.info("Database migrations applied successfully.")

except Exception as e:
    log.error(f"An error occurred during migrations: {e}", exc_info=True)
    exit(1)

log.info("Migration script finished successfully.") 