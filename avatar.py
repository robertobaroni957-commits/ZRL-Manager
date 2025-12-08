import os
import requests
from newZRL import create_app, db
from newZRL.models.wtrl_rider import WTRL_Rider

# --- Inizializza Flask app ---
app = create_app()

# --- Cartella dove salvare gli avatar ---
AVATAR_DIR = os.path.join(os.path.dirname(__file__), "newZRL/static/images/avatar")
os.makedirs(AVATAR_DIR, exist_ok=True)

with app.app_context():
    riders = WTRL_Rider.query.all()

    for r in riders:
        # Salta rider senza avatar
        if not r.avatar:
            continue

        # Salta se l'avatar è già locale (evita di riscaricare)
        if r.avatar.startswith("/static/images/avatar/") or r.avatar.startswith("/data/images/avatar/"):
            continue

        # Costruzione URL remoto
        if r.avatar.startswith("/uploads/"):
            url = "https://www.wtrl.racing" + r.avatar
        else:
            url = r.avatar

        # Nome file normalizzato: <profile_id>.jpeg
        filename = f"{r.profile_id}.jpeg"
        filepath = os.path.join(AVATAR_DIR, filename)

        # Scarica se non esiste già
        if not os.path.exists(filepath):
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Scaricato {filename}")
            except Exception as e:
                print(f"❌ Errore scaricando {url}: {e}")
                continue

        # Aggiorna campo avatar con percorso static compatibile Flask
        r.avatar = f"/static/images/avatar/{filename}"

    # Commit finale su DB
    db.session.commit()
    print("✅ Tutti gli avatar aggiornati nel DB")
