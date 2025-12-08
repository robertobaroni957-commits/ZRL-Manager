from newZRL import create_app, db

app = create_app()

def init_db():
    """Crea tutte le tabelle mancanti senza cancellare dati esistenti."""
    with app.app_context():
        db.create_all()
        print("✅ Database inizializzato")

if __name__ == "__main__":
    init_db()
    # Avvia Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
