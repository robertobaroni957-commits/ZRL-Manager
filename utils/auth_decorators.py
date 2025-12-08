# newZRL/utils/auth_decorators.py

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_user as flask_login_user, logout_user as flask_logout_user
from newZRL.models.user import User
from werkzeug.security import check_password_hash

# ============================================================
# 🔐 Decoratori di accesso basati sui ruoli
# ============================================================

def require_role(*allowed_roles):
    """Permette l'accesso solo a determinati ruoli."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in allowed_roles:
                flash("⛔ Accesso non autorizzato", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def require_admin(f):
    return require_role("admin")(f)

def require_moderator(f):
    return require_role("admin", "moderator")(f)

def require_captain(f):
    return require_role("captain")(f)

# ============================================================
# 🧑‍💼 Login e Logout utenti
# ============================================================

def login_user(email: str, password: str):
    """
    Login utente con SQLAlchemy + Flask-Login.
    Restituisce l'oggetto User se login riuscito, None altrimenti.
    """
    user = User.query.filter_by(email=email, active=True).first()
    if user and check_password_hash(user.password, password):
        flask_login_user(user)  # salva user in sessione automaticamente
        return user
    return None

def logout_user():
    """Logout utente."""
    flask_logout_user()

# ============================================================
# 🔐 Decoratore aggiuntivo per ruoli multipli
# ============================================================

def require_roles(allowed_roles):
    """Permette accesso solo a ruoli multipli definiti in allowed_roles (lista)."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in allowed_roles:
                flash("⛔ Accesso non autorizzato", "danger")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator
