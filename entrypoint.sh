#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==> [DEBUG] Starting entrypoint.sh..."

echo "==> [DEBUG] Checking environment variables..."
if [ -n "$SECRET_KEY" ]; then
    echo "DEBUG: SECRET_KEY is set."
else
    echo "DEBUG: SECRET_KEY is NOT set!"
fi
if [ -n "$DATABASE_URL" ]; then
    echo "DEBUG: DATABASE_URL is set."
else
    echo "DEBUG: DATABASE_URL is NOT set!"
fi

echo "==> [DEBUG] Activating virtual environment..."
# Render's build process should handle this, but it's safe to keep.
if [ -d ".venv" ]; then
    . .venv/bin/activate
fi

# Run database migrations
echo "==> [DEBUG] About to run python run_migrations.py..."
python run_migrations.py
echo "==> [DEBUG] Finished running python run_migrations.py."

# Start the application
echo "==> [DEBUG] About to start Gunicorn server..."
gunicorn --bind 0.0.0.0:${PORT} --log-level debug run:app
echo "==> [DEBUG] Gunicorn process finished. (This line should not be reached if the server runs correctly)."