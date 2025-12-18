import os
import json
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
import time
# Assicurati che questi siano importati correttamente
from newZRL import db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider 

from ..bp import admin_bp

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

import requests # Added this import

@admin_bp.route("/wtrl_import/import_teams", methods=["GET"]) # Changed route and method
@login_required
def import_wtrl_teams_and_riders_from_api():
    """Importa o aggiorna i dati dei team e dei rider WTRL direttamente dall'API."""
    try: # <--- Start of the new try block for the entire function
        # ... (existing code) ...

    @admin_bp.route("/wtrl_teams")
    @login_required
    def wtrl_teams_page():
        """Renders the WTRL Teams page, likely to display imported teams."""
        # This route will eventually fetch and display teams from the database.
        # For now, it just renders the template.
        return render_template("admin/wtrl_teams.html")

        # Read TRC IDs from the local file
        trc_list_file = os.path.join(current_app.root_path, "..", "data", "XXXteam_trc_list.txt")
        trc_list = []
        try:
            with open(trc_list_file, "r", encoding="utf-8") as f:
                trc_list = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("⚠️ File XXXteam_trc_list.txt non trovato.") # Changed flash to print
            return redirect(url_for("admin_bp.wtrl_teams_page"))

        if not trc_list:
            print("⚠️ Nessun TRC trovato nel file XXXteam_trc_list.txt.") # Changed flash to print
            return redirect(url_for("admin_bp.wtrl_teams_page"))

        teams_saved = 0
        riders_saved = 0
        skipped_riders = []
    
        # Season number for the API call (can be made dynamic later if needed)
        season_number = "17" 
        wtrl_api_base_url = f"https://www.wtrl.racing/api/zrl/{season_number}/teams/"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.wtrl.racing/",
            "wtrl-api-version": "2.7",
            "Cookie": current_app.config["WTRL_API_COOKIE"],
        }

        for trc_id in trc_list:
            print(f"--- Processing TRC: {trc_id} ---") # Debug print
            team_api_url = f"{wtrl_api_base_url}{trc_id}"
            try:
                resp = requests.get(team_api_url, headers=headers, timeout=12)
                resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                data = resp.json()

                meta = data.get("meta", {}) # The JSON structure seems to be similar to the old local files
            
                # --- 1. Estrazione Campi Team ---
                # ... (rest of the existing team and rider import logic, adapted to 'data' object) ...
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
                trc = safe_int(trc_id, default=None) # Use trc_id from the list
                if trc is None:
                    print(f"[WTRL Teams Import] TRC {trc_id} saltato: TRC non valido.") # Changed flash to print
                    continue

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
                    print(f"[WTRL Teams Import] Created Team: {team.name} (TRC: {team.trc})") # Debug print
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
                    print(f"[WTRL Teams Import] Updated Team: {team.name} (TRC: {team.trc})") # Debug print
                teams_saved += 1

                # --- 2. Importa e Aggiorna Rider ---
                for m in data.get("riders", []):
                    # Debug print for available rider IDs from team API
                    print(f"[WTRL Teams Import] Rider in Team API JSON: name={m.get('name')}, profileId={m.get('profileId')}, zid={m.get('zid')}, zwid={m.get('zwid')}")

                    # Prioritize zid, then zwid, then profileId
                    profile_id_source = m.get("zid") or m.get("zwid") or m.get("profileId")
                
                    # Conversione sicura di Profile ID
                    correct_profile_id_int = safe_int(profile_id_source, default=None)
                
                    if correct_profile_id_int is None:
                        skipped_riders.append(f"Rider senza profileId valido in TRC {trc}")
                        print(f"[WTRL Teams Import] Skipped rider in TRC {trc}: Missing or invalid profileId.") # Debug print
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
                        print(f"[WTRL Teams Import] Created Rider: {rider.name} (Profile ID: {rider.profile_id}, TRC: {rider.team_trc})") # Debug print
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
                        print(f"[WTRL Teams Import] Updated Rider: {rider.name} (Profile ID: {rider.profile_id}, TRC: {rider.team_trc})") # Debug print
                    riders_saved += 1
            
                db.session.commit() # Commit after each team for now.
                time.sleep(1) # Add a 1-second delay to avoid hitting API rate limits


            except requests.exceptions.RequestException as e:
                db.session.rollback()
                flash(f"⚠️ Errore fetchando TRC {trc_id} dall'API: {str(e)}. Rollback eseguito. **Il ciclo dovrebbe continuare.**", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"⚠️ Errore critico importando TRC {trc_id}: {str(e)}. Rollback eseguito. **Il ciclo dovrebbe continuare.**", "danger")
            
    
        final_message = f"✅ Import completato: {teams_saved} team, {riders_saved} riders salvati."
        if skipped_riders:
            final_message += f" Attenzione: {len(skipped_riders)} ciclisti saltati (profileId mancante o non valido)."
        print(final_message) # Debug print
    
        flash(final_message, "info") # Flash still used for web interface

        return redirect(url_for("admin_bp.wtrl_teams_page")) # Redirect to teams page
except Exception as e: # <--- Start of the new except block for general errors
    db.session.rollback()
    flash(f"❌ Si è verificato un errore inatteso durante l'importazione: {str(e)}", "danger")
    return redirect(url_for("admin_bp.wtrl_teams_page")) # Redirect to teams page in case of a general error
