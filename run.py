from newZRL import create_app, db
from flask_migrate import Migrate
import os

app = create_app()

# -----------------------------
# Inizializza Flask-Migrate
# -----------------------------
migrate = Migrate(app, db)


# -----------------------------
# Creazione tabelle iniziali
# -----------------------------
def init_db():
    """Crea tutte le tabelle mancanti senza cancellare dati esistenti."""
    with app.app_context():
        db.create_all()
        print("✅ Database inizializzato")

# -----------------------------
# Avvio dell'app
# -----------------------------
if __name__ == "__main__":
    init_db()  # crea tabelle se mancanti
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
