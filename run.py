# run.py
from newZRL import create_app, db
import webbrowser
import os

app = create_app()

def init_db():
    """Crea tutte le tabelle se non esistono ancora."""
    with app.app_context():
        db.create_all()
        print("✅ Database inizializzato (tabelle create)")

if __name__ == "__main__":
    # Inizializza il database
    init_db()

    # Apri il browser locale (solo se in locale)
    if os.environ.get("FLASK_ENV") != "production":
        webbrowser.open("http://127.0.0.1:5000/")

    # Usa la porta di Render o fallback a 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
