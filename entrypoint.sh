#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Print a message and run database migrations
echo "Running database migrations..."
flask db upgrade
echo "Migrations complete."

# Print a message and start the main application
echo "Starting application server..."
waitress-serve --host=0.0.0.0 --port=${PORT} run:app
