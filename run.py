# run.py
import os
import logging
import sys
from waitress import serve
from newZRL import create_app, db # Ensure db is imported if used directly here, but it's passed to create_app
from flask_migrate import Migrate, upgrade # Import Flask-Migrate

# Configure logging for the Waitress server
# This ensures that logs are always directed to stdout
logging.basicConfig(
    level=logging.INFO, # Or logging.DEBUG if more verbose output is needed
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

app = create_app(os.getenv("FLASK_CONFIG") or "development")

# Initialize Flask-Migrate
migrate = Migrate(app, db) # Initialize Migrate with the app and db

if __name__ == "__main__":
    # In production, run migrations on startup
    if os.environ.get("FLASK_CONFIG") == "production":
        with app.app_context():
            upgrade()

    if os.environ.get("FLASK_DEBUG") == "1":
        # Development server
        port = int(os.environ.get("PORT", 5000)) # Use PORT env var for dev as well
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Production server
        port = int(os.environ.get("PORT", 5000)) # Ensure PORT env var is used for production
        serve(app, host="0.0.0.0", port=port)