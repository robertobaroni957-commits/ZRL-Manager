from flask import Blueprint, url_for, redirect, render_template
from flask_login import current_user
from flask import has_request_context
from newZRL.blueprints.admin.bp import admin_bp # Import admin_bp
from newZRL.blueprints.captain.routes import captain_bp # Import captain_bp

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
            return redirect(url_for("dashboard_captain.captain_dashboard"))
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

@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500
