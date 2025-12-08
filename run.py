# run.py
import os
from newZRL import create_app

app = create_app()

if __name__ == "__main__":
    # Porta: usa quella fornita da Render, fallback a 5000 per locale
    port = int(os.environ.get("PORT", 5000))
    # Host 0.0.0.0 per permettere accesso esterno su Render
    app.run(host="0.0.0.0", port=port, debug=True)
