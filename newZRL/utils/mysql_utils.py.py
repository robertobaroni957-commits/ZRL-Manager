import os
import pymysql
import logging
from flask import g, has_app_context
from werkzeug.security import generate_password_hash, check_password_hash

# ===============================================================
# 🔌 CONNESSIONE DATABASE MySQL
# ===============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "RB",
    "password": "Ro12ba-12",
    "database": "zrl",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

def _connect_db(attr_name):
    """Crea o riusa una connessione MySQL."""
    if has_app_context():
        if not hasattr(g, attr_name):
            conn = pymysql.connect(**DB_CONFIG)
            setattr(g, attr_name, conn)
            logging.info(f"📂 Connessione Flask attiva → MySQL")
        return getattr(g, attr_name)

    conn = pymysql.connect(**DB_CONFIG)
    logging.info(f"📂 Connessione diretta → MySQL")
    return conn

def get_db():
    """Connessione principale al DB ZRL (MySQL)."""
    return _connect_db("zrl_db")

def close_db(e=None):
    """Chiude la connessione se esiste."""
    db = g.pop("zrl_db", None)
    if db is not None:
        db.close()

# ===============================================================
# 👤 GESTIONE ADMIN
# ===============================================================

def get_admin_by_username(username):
    """Recupera un admin dal database per username."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cur.fetchone()
    print("🔍 Admin trovato:", admin if admin else "Nessuno")
    return admin

def create_admin(username, password, email=None):
    """Crea un nuovo admin (se non esiste già)."""
    conn = get_db()
    hashed_pw = generate_password_hash(password)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO admins (username, password, email)
                VALUES (%s, %s, %s)
            """, (username, hashed_pw, email))
        conn.commit()
        print(f"✅ Admin '{username}' creato con successo")
    except pymysql.err.IntegrityError:
        print(f"⚠️ Admin '{username}' già esistente")

def verify_admin_password(admin_row, password):
    """Verifica la password di un admin."""
    if not admin_row:
        print("⚠️ Nessun admin da verificare")
        return False
    result = check_password_hash(admin_row["password"], password)
    print("🔐 Verifica password:", result)
    return result
