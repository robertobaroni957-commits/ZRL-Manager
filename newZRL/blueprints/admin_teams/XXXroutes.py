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

@admin_teams_bp.route("/", methods=["GET", "POST"])
@login_required
@require_admin
def manage_teams():
    if request.method == "POST" and request.form.get("action") == "create":
        team = Team(
            name=request.form["name"].strip(),
            category=request.form["category"],
            division=request.form["division"]
        )
        db.session.add(team)
        db.session.commit()
        flash("✅ Team creato con successo!", "success")
        return redirect(url_for("admin_teams.manage_teams"))

    teams = Team.query.all()
    riders = Rider.query.filter_by(active=True).all()
    return render_template("admin/manage_teams.html", teams=teams, riders=riders)

@admin_teams_bp.route("/<int:team_id>/members", methods=["GET", "POST"])
@login_required
@require_admin
def manage_team_members(team_id):
    team = Team.query.get_or_404(team_id)
    riders = team.members  # lista riders assegnati al team
    assigned_rider_ids = [r.zwift_power_id for r in riders]
    category_riders = Rider.query.filter_by(category=team.category, active=True).all()
    captain = next((r for r in riders if r.is_captain), None)

    return render_template(
        "admin/manage_team_members.html",
        team=team,
        riders=riders,
        category_riders=category_riders,
        assigned_rider_ids=assigned_rider_ids,
        captain=captain
    )
