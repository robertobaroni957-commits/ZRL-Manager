import os
import sqlite3
from werkzeug.security import generate_password_hash
from newZRL import create_app
from newZRL.models import db
from newZRL.models.user import User
from newZRL.models.rider import Rider  # esempio se hai altri modelli
from newZRL.models.team import Team

# --- CONFIG ---
SQLITE_DB = "zrl.db"  # vecchio db SQLite
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "secure123"
ADMIN_ZWIFT_ID = "123456"

# --- CREAZIONE APP E CONTESTO ---
app = create_app()

def main():
    with app.app_context():
        # 1️⃣ CREA TUTTE LE TABELLE MYSQL
        print("🔹 Creazione tabelle MySQL...")
        db.create_all()
        print("✅ Tabelle create!")

        # 2️⃣ MIGRA DATI DA SQLITE (opzionale)
        if os.path.exists(SQLITE_DB):
            print("🔹 Migrazione dati da SQLite...")
            conn_sqlite = sqlite3.connect(SQLITE_DB)
            conn_sqlite.row_factory = sqlite3.Row
            cur = conn_sqlite.cursor()

            # Esempio: migrazione utenti
            try:
                cur.execute("SELECT * FROM users")
                users = cur.fetchall()
                for u in users:
                    if not User.query.filter_by(email=u['email']).first():
                        hashed_pw = u['password']  # se già hashato
                        user = User(
                            email=u['email'],
                            password=hashed_pw,
                            zwift_power_id=u['zwift_power_id'],
                            role=u['role'],
                            team_id=u['team_id'],
                            active=u['active']
                        )
                        db.session.add(user)
                db.session.commit()
                print(f"✅ Migrazione utenti completata ({len(users)} record).")
            except Exception as e:
                print(f"❌ Errore migrazione utenti: {e}")
            finally:
                conn_sqlite.close()
        else:
            print("⚠️ Nessun file SQLite trovato, salto migrazione dati.")

        # 3️⃣ CREA ADMIN INIZIALE SE NON ESISTE
        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            hashed_pw = generate_password_hash(ADMIN_PASSWORD)
            admin_user = User(
                email=ADMIN_EMAIL,
                password=hashed_pw,
                zwift_power_id=ADMIN_ZWIFT_ID,
                role="admin",
                active=1
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Admin '{ADMIN_EMAIL}' creato.")
        else:
            print(f"⚠️ Admin '{ADMIN_EMAIL}' già presente.")

if __name__ == '__main__':
    main()
