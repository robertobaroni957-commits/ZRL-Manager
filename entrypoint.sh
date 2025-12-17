#!/bin/sh

echo "Entrypoint script started!" # Debug message

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
python run_migrations.py
echo "Migrations complete."

# Print a message and start the main application
echo "Starting application server..."
waitress-serve --host=0.0.0.0 --port=${PORT} run:app
