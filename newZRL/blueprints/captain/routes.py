# newZRL/blueprints/captain/routes.py
from flask import Blueprint, render_template

captain_bp = Blueprint("dashboard_captain", __name__, url_prefix="/captain")

@captain_bp.route("/dashboard")
def captain_dashboard():
    return render_template("captain/dashboard.html", title="Dashboard Capitano")
