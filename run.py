# run.py
import os
import logging
import sys
from waitress import serve
from newZRL import create_app, db 

if __name__ == "__main__":
    if os.environ.get("FLASK_DEBUG") == "1":
        # Development server
        port = int(os.environ.get("PORT", 5000)) # Use PORT env var for dev as well
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Production server
        port = int(os.environ.get("PORT", 5000)) # Ensure PORT env var is used for production
        serve(app, host="0.0.0.0", port=port)