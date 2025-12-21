from werkzeug.security import generate_password_hash
from newZRL import create_app
from newZRL.models.user import User, db

app = create_app('production')
with app.app_context():
    user = User.query.filter_by(email="admin@teaminox.it").first()
    password_hash = generate_password_hash("password123")

    if user:
        # Se l'utente esiste, aggiornalo per essere sicuro che sia corretto
        user.password = password_hash
        user.role = "admin"
        user.active = True
        print("🔄 Admin esistente, password e ruolo aggiornati.")
    else:
        # Se non esiste, crealo
        user = User(
            profile_id=123456,
            email="admin@teaminox.it",
            password=password_hash,
            role="admin",
            active=True
        )
        db.session.add(user)
        print("✅ Nuovo admin creato.")
    
    db.session.commit()
    print("Database committato con successo.")
