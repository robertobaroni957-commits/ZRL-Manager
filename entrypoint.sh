#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==> Starting entrypoint.sh for ZRL Manager"

# Ensure the virtual environment's python is used
# This assumes the venv is created in .venv/
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    . .venv/bin/activate
fi

# Run database migrations
echo "Running database migrations..."
export ALEMBIC_CONFIG=./alembic.ini # Explicitly tell Alembic where to find alembic.ini
python run_migrations.py # Use 'python' instead of 'py'
echo "Database migrations complete."

# Start the application
echo "Starting application server..."
# Ensure Flask application is discoverable for waitress if not handled by run.py
# If FLASK_APP is needed here, set it explicitly or ensure run.py creates the app directly.
waitress-serve --host=0.0.0.0 --port=${PORT} run:app

echo "Entrypoint finished."