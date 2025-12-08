# newZRL/blueprints/admin/dashboard.py

from .bp import admin_bp
from flask import render_template
from flask_login import login_required
from datetime import date
from newZRL import db

from newZRL.models.team import Team
from newZRL.models.race import Race
from newZRL.models.round import Round
from newZRL.models.race_lineup import RaceLineup
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.utils.race_utils import get_next_race_date
from utils.auth_decorators import require_roles


@admin_bp.route("/dashboard")
@login_required
@require_roles(["admin", "captain"])
def dashboard():
    current_time = date.today()

    # Trova il round attivo
    current_round = Round.query.filter_by(is_active=True).first()

    # Carica le gare del round attivo
    races = (
        Race.query.filter_by(round_id=current_round.id)
        .order_by(Race.race_date)
        .all()
        if current_round else []
    )

    # Carica tutti i team
    teams = Team.query.order_by(Team.name).all()

    # Pre-calcolo: lineup presente e prossima gara per ogni team
    for t in teams:
        # Ha almeno una lineup registrata?
        # Usa la colonna numerica team_trc senza join stringhe
        t.has_lineup = RaceLineup.query.join(WTRL_Rider).filter(WTRL_Rider.team_trc == t.trc).first() is not None

        # Trova il capitano tramite captain_profile_id
        t.captain_name = "—"
        if t.captain_profile_id:
            captain = WTRL_Rider.query.filter_by(profile_id=t.captain_profile_id).first()
            if captain:
                t.captain_name = captain.name

        # Prossima gara programmata per il team
        t.next_race_date = get_next_race_date(t.trc)

    return render_template(
        "admin/admin_dashboard.html",
        current_round=current_round,
        races=races,
        teams=teams,
        current_time=current_time
    )
