from flask import Blueprint, url_for, redirect, render_template
from flask_login import current_user
from flask import has_request_context
main_bp = Blueprint("main", __name__)

def redirect_based_on_role():
    if not has_request_context():
        return None  # nessuna request attiva
    
    if current_user.is_authenticated:
        role = getattr(current_user, "role", None)
        if role == "admin":
            # import lazy solo del blueprint, mai di dashboard.py
            from newZRL.blueprints.admin.bp import admin_bp
            return redirect(url_for("admin_bp.dashboard"))
        elif role == "captain":
            from newZRL.blueprints.admin.teams.bp import admin_teams_bp
            return redirect(url_for("admin_teams_bp.manage_teams"))
    return None


@main_bp.route("/")
def index():
    redirect_resp = redirect_based_on_role()
    if redirect_resp:
        return redirect_resp
    return redirect(url_for("auth.login"))

@main_bp.route("/welcome")
def welcome():
    redirect_resp = redirect_based_on_role()
    if redirect_resp:
        return redirect_resp
    return render_template("welcome.html")
