# run.py
import os
from waitress import serve
from newZRL import create_app

# Crea l'app
app = create_app("production") 

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    if os.environ.get("FLASK_DEBUG") == "1":
        # Dev server
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Production server con Waitress
        serve(app, host="0.0.0.0", port=port)
