#!/bin/sh

echo "Entrypoint script started!"
echo "DEBUG: This is the simplified entrypoint.sh"
echo "DEBUG: PATH is: $PATH"
echo "DEBUG: FLASK_APP is: $FLASK_APP"
echo "DEBUG: FLASK_CONFIG is: $FLASK_CONFIG"
echo "DEBUG: PROD_DATABASE_URL is: $PROD_DATABASE_URL"

# This script will now just exit after printing debug info
# We expect Render to mark the service unhealthy or restart it.
# We are looking for these debug messages in the logs.
exit 0
