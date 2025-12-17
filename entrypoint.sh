#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

echo "==> Starting entrypoint.sh for newZRL"

# -----------------------------
# 1️⃣ Controllo variabili d'ambiente
# -----------------------------
: "${PROD_DATABASE_URL:?PROD_DATABASE_URL must be set}"
: "${SECRET_KEY:?SECRET_KEY must be set}"

echo "Using PROD_DATABASE_URL and SECRET_KEY environment variables."

# -----------------------------
# 2️⃣ Migrazioni database
# -----------------------------
echo "Running database migrations..."
py -3.13 -m flask --app newZRL:create_app db upgrade
echo "Database migrations complete."

# -----------------------------
# 3️⃣ Avvio server con Waitress
# -----------------------------
PORT=${PORT:-5000}
echo "Starting production server on port $PORT..."
py -3.13 run.py

echo "Entrypoint finished."
