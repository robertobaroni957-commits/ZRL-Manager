import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
# Assicurati che questi siano importati correttamente
from newZRL import db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider 

# Directory dei JSON
JSON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "wtrl_json"))

wtrl_import_bp = Blueprint("wtrl_import", __name__, url_prefix="/admin/wtrl_import")

# ==============================================================================
# FUNZIONI DI SUPPORTO PER L'INTEGRITÀ LOGICA E DEI TIPI DI DATO
# ==============================================================================

def safe_float(val, default=None):
    """Tenta di convertire un valore in float, restituendo il default in caso di errore o se è vuoto/None."""
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=None):
    """Tenta di convertire un valore in int, restituendo il default in caso di errore o se è vuoto/None."""
    if val is None or val == "":
        return default
    try:
        # A volte i JSON contengono numeri come stringhe float (es. "1.0"). 
        # Convertiamo prima a float per gestirli, poi a int.
        return int(float(val)) 
    except (ValueError, TypeError):
        return default

def safe_bool_to_int(val, default=0):
    """Converte un valore in 1 (True) o 0 (False) per i campi INT booleani."""
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, str):
        if val.lower() in ('true', '1'):
            return 1
        if val.lower() in ('false', '0'):
            return 0
    return default 

# ==============================================================================
# ROUTE PRINCIPALE DI IMPORTAZIONE
# ==============================================================================

@wtrl_import_bp.route("/import_all", methods=["GET", "POST"])
@login_required
def import_teams_and_riders():
    """Importa o aggiorna i dati dei team e dei rider WTRL da tutti i file JSON."""
    if request.method == "POST":
        json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]
        teams_saved = 0
        riders_saved = 0
        skipped_riders = []

        for filename in json_files:
            try:
                with open(os.path.join(JSON_DIR, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)

                meta = data.get("meta", {})
                trc_raw = meta.get("trc") 
                
                # Conversione sicura in INT per il TRC del team
                trc = safe_int(trc_raw, default=None)
                if trc is None:
                    flash(f"File {filename} saltato: TRC mancante o non valido nel blocco meta.", "warning")
                    continue
                
                # --- 1. Estrazione Campi Team ---
                # ... (Logica di estrazione dei campi team, invariata dalle ultime correzioni)
                division = meta.get("division")
                team_info = meta.get("team", {})
                competition = meta.get("competition", {})
                captain_info = meta.get("administrators", {}).get("captain", {})

                team_name = team_info.get("name")
                captain_name_val = f"{captain_info.get('firstName', '')} {captain_info.get('lastName', '')}".strip() or None
                captain_profile_id = captain_info.get("profileId")
                wtrl_team_id = team_info.get("teamid") or team_info.get("tttid") or None
                jersey_name = team_info.get("jerseyname") or None
                jersey_image = team_info.get("jerseyimage") or None
                recruiting = safe_bool_to_int(team_info.get("recruiting"), default=0)
                is_dev = safe_bool_to_int(team_info.get("isdev"), default=0)
                competition_class = competition.get("class") or None
                competition_season = competition.get("season") or None
                competition_year = competition.get("sportsYear") or None
                competition_round = competition.get("roundnumber") or None
                competition_status = competition.get("status") or None
                member_count = safe_int(meta.get("memberCount"), default=0)
                members_remaining = safe_int(meta.get("membersRemaining"), default=0)

                # CREA/AGGIORNA TEAM
                team = Team.query.filter_by(trc=trc).first()
                if not team:
                    team = Team(
                        trc=trc, # TRC è un INT
                        name=team_name,
                        division=division,
                        wtrl_team_id=wtrl_team_id,
                        jersey_name=jersey_name,
                        jersey_image=jersey_image,
                        recruiting=recruiting,
                        is_dev=is_dev,
                        competition_class=competition_class,
                        competition_season=competition_season,
                        competition_year=competition_year,
                        competition_round=competition_round,
                        competition_status=competition_status,
                        member_count=member_count,
                        members_remaining=members_remaining,
                        captain_name=captain_name_val,
                        captain_profile_id=captain_profile_id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(team)
                else:
                    team.name = team_name
                    team.division = division
                    team.wtrl_team_id = wtrl_team_id
                    team.jersey_name = jersey_name
                    team.jersey_image = jersey_image
                    team.recruiting = recruiting
                    team.is_dev = is_dev
                    team.competition_class = competition_class
                    team.competition_season = competition_season
                    team.competition_year = competition_year
                    team.competition_round = competition_round
                    team.competition_status = competition_status
                    team.member_count = member_count
                    team.members_remaining = members_remaining
                    team.captain_name = captain_name_val
                    team.captain_profile_id = captain_profile_id
                    team.updated_at = datetime.utcnow()
                teams_saved += 1

                # --- 2. Importa e Aggiorna Rider ---
                for m in data.get("riders", []):
                    profile_id_raw = m.get("profileId")
                    
                    # Conversione sicura di Profile ID
                    correct_profile_id_int = safe_int(profile_id_raw, default=None)
                    
                    if correct_profile_id_int is None:
                        skipped_riders.append(f"Rider senza profileId valido in TRC {trc}")
                        continue

                    # COERENZA: Costruzione della chiave primaria composita (TRC/ProfileID)
                    rider_id = f"{trc}/{correct_profile_id_int}" 
                    rider = WTRL_Rider.query.filter_by(id=rider_id).first()
                        
                    # Conversione robusta per i valori float
                    zftp_val = safe_float(m.get("zftp"), default=None)
                    zftpw_val = safe_float(m.get("zftpw"), default=None)
                    zmap_val = safe_float(m.get("zmap"), default=None)
                    zmapw_val = safe_float(m.get("zmapw"), default=None)

                    # Campi interi, usiamo safe_int con default 0
                    riderpoints_val = safe_int(m.get("riderpoints"), default=0)
                    teams_val = safe_int(m.get("teams"), default=0)
                    appearances_round_val = safe_int(m.get("appearancesRound"), default=0)
                    appearances_season_val = safe_int(m.get("appearancesSeason"), default=0)


                    if not rider:
                        rider = WTRL_Rider(
                            id=rider_id,
                            team_trc=trc,                       # <-- TRC INT corretto dal meta
                            profile_id=correct_profile_id_int,  # <-- Profile ID INT corretto
                            tmuid=m.get("tmuid") or None,
                            name=m.get("name"),
                            avatar=m.get("avatar") or None,
                            member_status=m.get("memberStatus"),
                            signedup=m.get("signedup", False),
                            category=m.get("category"),
                            zftp=zftp_val,
                            zftpw=zftpw_val,
                            zmap=zmap_val,
                            zmapw=zmapw_val,
                            riderpoints=riderpoints_val,
                            teams=teams_val,
                            appearances_round=appearances_round_val,
                            appearances_season=appearances_season_val,
                            user_id=m.get("userId"),
                            created_at=datetime.utcnow()
                        )
                        db.session.add(rider)
                        riders_saved += 1
                    else:
                        # Aggiorna rider esistente
                        rider.team_trc = trc                       # <-- TRC INT corretto dal meta
                        rider.profile_id = correct_profile_id_int  # <-- Profile ID INT corretto
                        rider.tmuid = m.get("tmuid") or None
                        rider.name = m.get("name")
                        rider.avatar = m.get("avatar") or None
                        rider.member_status = m.get("memberStatus")
                        rider.signedup = m.get("signedup", False)
                        rider.category = m.get("category")
                        rider.zftp = zftp_val
                        rider.zftpw = zftpw_val
                        rider.zmap = zmap_val
                        rider.zmapw = zmapw_val
                        rider.riderpoints = riderpoints_val
                        rider.teams = teams_val
                        rider.appearances_round = appearances_round_val
                        rider.appearances_season = appearances_season_val
                        rider.user_id = m.get("userId")
                        rider.updated_at = datetime.utcnow()
                        riders_saved += 1
                
                db.session.commit() # Commit dopo ogni file, come da flusso corretto

            except Exception as e:
                db.session.rollback()
                flash(f"⚠️ Errore critico importando {filename} (TRC {trc}): {str(e)}. Rollback eseguito. **Il ciclo dovrebbe continuare.**", "error")
                
        
        final_message = f"✅ Import completato: {teams_saved} team, {riders_saved} riders salvati."
        if skipped_riders:
            final_message += f" Attenzione: {len(skipped_riders)} ciclisti saltati (profileId mancante o non valido)."
            
        flash(final_message, "info")

        return redirect(url_for("wtrl_import.import_teams_and_riders"))

    # Recupera tutti i team per la visualizzazione
    teams = Team.query.order_by(Team.name).all()
    return render_template("admin/wtrl_teams.html", teams=teams)