from flask import render_template, session # Import session
from flask_login import login_required, current_user # Import current_user
from datetime import date
from newZRL import db
from newZRL.blueprints.admin.bp import admin_bp
from newZRL.models.team import Team
from newZRL.models.race import Race
from newZRL.models.round import Round
from newZRL.models.race_lineup import RaceLineup
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.utils.race_utils import get_next_race_date
from utils.auth_decorators import require_roles
from sqlalchemy.orm import joinedload
from newZRL.models.user import User # Import User model

@admin_bp.route("/dashboard")
@login_required
@require_roles(["admin", "captain"])
def dashboard():
    current_time = date.today()

    # Find the active round
    current_round = Round.query.filter_by(is_active=True).first()

    # Load races for the active round
    races = (
        Race.query.filter_by(round_id=current_round.id)
        .order_by(Race.race_date)
        .all()
        if current_round else []
    )

    # Filter teams based on user role
    if current_user.is_authenticated and current_user.role == "captain":
        # For captains, find their team based on their profile_id
        # Assuming current_user.profile_id holds the captain's profile ID
        teams = Team.query.filter_by(captain_profile_id=current_user.profile_id).order_by(Team.name).all()
        if not teams:
            # If a captain has no assigned team, show an empty list
            teams = []
            flash("Non sei assegnato a nessun team come capitano.", "warning")
    else:
        # For admins, load all teams
        teams = Team.query.order_by(Team.name).all()

    # Efficiently pre-load all captains for the displayed teams
    captain_ids = {t.captain_profile_id for t in teams if t.captain_profile_id}
    if captain_ids:
        captains = User.query.filter(User.profile_id.in_(captain_ids)).all()
        captain_map = {c.profile_id: c for c in captains}
    else:
        captain_map = {}

    # Pre-calculation: lineup present, captain name, and next race for each team
    for t in teams:
        # Has at least one registered lineup?
        t.has_lineup = RaceLineup.query.join(WTRL_Rider).filter(WTRL_Rider.team_trc == t.trc).first() is not None

        # Find captain from the pre-loaded map
        captain = captain_map.get(t.captain_profile_id)
        if captain:
            t.captain_name = captain.email.split('@')[0].capitalize()
        else:
            t.captain_name = "—"

        # Next scheduled race for the team
        t.next_race_date = get_next_race_date(t.trc)

    return render_template(
        "admin/admin_dashboard.html",
        current_round=current_round,
        races=races,
        teams=teams,
        current_time=current_time
    )
