#!/bin/sh
set -e  # Exit immediately if a command exits with a non-zero status

echo "Running database migrations..."
python -m flask --app newZRL:create_app db upgrade

echo "Starting application server..."
# Usa Waitress per servire l'app su Render
# $PORT è impostata automaticamente dall'ambiente Render
exec waitress-serve --listen=0.0.0.0:$PORT run:app
