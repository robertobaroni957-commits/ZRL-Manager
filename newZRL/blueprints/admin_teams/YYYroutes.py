from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from newZRL.models.team import Team
from newZRL.models.rider import Rider
from newZRL import db

admin_teams_bp = Blueprint("admin_teams", __name__, url_prefix="/admin/teams")

def require_admin(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("⛔ Accesso riservato agli amministratori", "danger")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper

