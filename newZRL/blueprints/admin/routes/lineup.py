from ..bp import admin_bp
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from newZRL import db
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
import logging

from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models.team import Team
from newZRL.models.race_lineup import RaceLineup
from newZRL.utils.race_utils import get_next_race_date
from utils.auth_decorators import require_roles

logger = logging.getLogger(__name__)


def parse_date(value):
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        pass
    return None


@admin_bp.route("/manage_lineup/<trc>/<race_date>", methods=["GET", "POST"])
@require_roles(["admin", "captain"])
@login_required
def manage_lineup(trc, race_date):
    # --- Team ---
    try:
        trc_int = int(trc)
    except ValueError:
        flash("❌ TRC non valido", "danger")
        return redirect(url_for('main.index'))

    team = Team.query.filter_by(trc=trc_int).first()
    if not team:
        flash("❌ Team non trovato", "danger")
        return render_template("admin/manage_lineup.html", error=True)

    # --- Race Date ---
    if race_date == "next":
        next_date = get_next_race_date(trc_int)
        if not next_date:
            flash("⛔ Nessuna gara programmata", "warning")
            return render_template("admin/manage_lineup.html", error=True)
        race_date_obj = parse_date(next_date)
    else:
        race_date_obj = parse_date(race_date)

    if not race_date_obj:
        flash("❌ Formato data non valido", "danger")
        return redirect(url_for('main.index'))

    race_date_str = race_date_obj.isoformat()
    race_id = f"{trc}_{race_date_obj.strftime('%Y%m%d')}"

    # --- POST ---
    if request.method == "POST":
        action = request.form.get("action")
        selected_riders = [int(rid) for rid in request.form.getlist("riders[]") if rid.isdigit()]

        if action == "save_lineup":
            if len(selected_riders) > 6:
                flash("⚠️ Puoi selezionare al massimo 6 rider", "warning")
            else:
                conflicting = []
                for rid in selected_riders:
                    conflict = RaceLineup.query.filter(
                        RaceLineup.race_date == race_date_obj,
                        RaceLineup.profile_id == rid,
                        RaceLineup.team_trc != trc_int
                    ).first()
                    if conflict:
                        r = WTRL_Rider.query.filter_by(profile_id=rid).first()
                        if r:
                            conflicting.append(r.name)
                if conflicting:
                    flash(f"❌ Rider già assegnati ad altri team: {', '.join(conflicting)}", "danger")
                else:
                    try:
                        existing = RaceLineup.query.filter_by(race_id=race_id).all()
                        existing_ids = {int(rl.profile_id) for rl in existing}

                        # Rimuovo quelli non selezionati
                        for rl in existing:
                            if int(rl.profile_id) not in selected_riders:
                                db.session.delete(rl)

                        # Aggiungo i nuovi
                        for rid in selected_riders:
                            if rid not in existing_ids:
                                db.session.add(RaceLineup(
                                    team_trc=trc_int,
                                    race_date=race_date_obj,
                                    profile_id=rid,
                                    race_id=race_id
                                ))
                        db.session.commit()
                        flash("✅ Lineup salvata correttamente", "success")
                    except IntegrityError as e:
                        db.session.rollback()
                        logger.error(f"IntegrityError: {e}")
                        flash("❌ Errore database: duplicato o integrità violata", "danger")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Commit Error: {e}")
                        flash("❌ Errore interno durante il salvataggio", "danger")

        elif action == "remove_rider":
            rid_str = request.form.get("remove_id")
            if rid_str and rid_str.isdigit():
                rid = int(rid_str)
                rl = RaceLineup.query.filter_by(race_id=race_id, profile_id=rid).first()
                if rl:
                    r = WTRL_Rider.query.filter_by(profile_id=rid).first()
                    db.session.delete(rl)
                    db.session.commit()
                    flash(f"🗑️ Rider {r.name if r else 'sconosciuto'} rimosso", "success")
            return redirect(url_for('admin_bp.manage_lineup', trc=trc, race_date=race_date_str))

        return redirect(url_for('admin_bp.manage_lineup', trc=trc, race_date=race_date_str))

    # --- GET ---
    riders = WTRL_Rider.query.filter_by(team_trc=trc_int).filter(
        WTRL_Rider.member_status != "REMOVED-CATEGORY"
    ).order_by(WTRL_Rider.name.asc()).all()

    selected_ids = {int(rl.profile_id) for rl in RaceLineup.query.filter_by(race_id=race_id).all()}
    busy_riders = {
        int(rl.profile_id) for rl in RaceLineup.query.filter(
            RaceLineup.race_date == race_date_obj,
            RaceLineup.team_trc != trc_int
        ).all()
    }

    return render_template(
        "admin/manage_lineup.html",
        trc=trc_int,
        race_date=race_date_str,
        team_name=team.name,
        riders=riders,
        selected_ids=selected_ids,
        assigned_captain=team.captain_name,
        busy_riders=busy_riders
    )
