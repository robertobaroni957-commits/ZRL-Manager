import os
import json
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
import time
import logging # Import logging
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError

# Configure a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Changed to INFO to capture more details
# Create a file handler for the error log
log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'wtrl_api_errors.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


# Assicurati che questi siano importati correttamente
from newZRL import db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider 

from ..bp import admin_bp

# ==============================================================================
# FUNZIONI DI SUPPORTO PER L'INTEGRITÀ LOGICA E DEI TIPI DI DATO
# ==============================================================================

def safe_float(val, default=0.0):
    """Tenta di convertire un valore in float, restituendo il default in caso di errore o se è vuoto/None."""
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
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

import threading
import requests
from .import_status import import_status_data

def run_import_in_background(app, season_number):
    """This function runs in a background thread to prevent a web request timeout."""
    with app.app_context():
        try:
            import_status_data['is_running'] = True
            import_status_data['progress'] = 0
            import_status_data['message'] = 'Inizio importazione...'

            trc_list_file = os.path.join(app.root_path, "..", "data", "team_trc_list.txt")
            trc_list = []
            try:
                with open(trc_list_file, "r", encoding="utf-8") as f:
                    trc_list = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                import_status_data['message'] = "Errore: File team_trc_list.txt non trovato."
                import_status_data['is_running'] = False
                return

            if not trc_list:
                import_status_data['message'] = "Errore: Nessun TRC trovato nel file team_trc_list.txt."
                import_status_data['is_running'] = False
                return

            teams_saved = 0
            riders_saved = 0
            skipped_riders = []
            total_trcs = len(trc_list)
            
            wtrl_api_base_url = f"https://www.wtrl.racing/api/zrl/{season_number}/teams/"
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.wtrl.racing/",
                "wtrl-api-version": "2.7",
                "Cookie": app.config["WTRL_API_COOKIE"],
            }
            response_save_dir = os.path.join(app.root_path, "data", "wtrl_json")
            os.makedirs(response_save_dir, exist_ok=True)

            for i, trc_id in enumerate(trc_list):
                progress = int(((i + 1) / total_trcs) * 100)
                import_status_data['progress'] = progress
                import_status_data['message'] = f"Processando TRC {trc_id} ({i+1}/{total_trcs})..."
                
                logger.info(f"--- Processing TRC: {trc_id} ---")
                team_api_url = f"{wtrl_api_base_url}{trc_id}"
                try:
                    data = None
                    for attempt in range(3):  # Retry up to 3 times
                        try:
                            # Use a longer timeout and a retry mechanism
                            resp = requests.get(team_api_url, headers=headers, timeout=60)
                            resp.raise_for_status()  # Raise an exception for bad status codes
                            data = resp.json()
                            break  # If successful, exit the loop
                        except requests.exceptions.ReadTimeout:
                            logger.warning(f"Timeout on attempt {attempt + 1} for TRC {trc_id}. Retrying in 5s...")
                            if attempt < 2:
                                time.sleep(5)  # Wait for 5 seconds before the next attempt
                            else:
                                logger.error(f"Final attempt failed for TRC {trc_id}. Skipping.")
                                raise # Re-raise the exception on the last attempt to be caught by the outer block
                    
                    if data is None:
                        # This would happen if all retries failed and the exception was caught outside
                        continue

                    response_file_path = os.path.join(response_save_dir, f"team_{trc_id}.json")
                    with open(response_file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    logger.info(f"Saved API response for TRC {trc_id} to {response_file_path}")

                    meta = data.get("meta", {})
                    division_from_meta = meta.get("division")
                    team_info = meta.get("team", {})
                    competition = meta.get("competition", {})
                    captain_info = meta.get("administrators", {}).get("captain", {})
                    competition_division = competition.get("division")
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

                    trc = safe_int(trc_id, default=None)
                    if trc is None:
                        logger.warning(f"Skipped TRC {trc_id}: invalid TRC ID.")
                        continue
                    
                    team = Team.query.filter_by(trc=trc).first()
                    if not team:
                        team = Team(
                            trc=trc, name=team_name, division=division_from_meta, category=competition_division,
                            wtrl_team_id=wtrl_team_id, jersey_name=jersey_name, jersey_image=jersey_image,
                            recruiting=recruiting, is_dev=is_dev, competition_class=competition_class,
                            competition_season=competition_season, competition_year=competition_year,
                            competition_round=competition_round, competition_status=competition_status,
                            member_count=member_count, members_remaining=members_remaining,
                            captain_name=captain_name_val, captain_profile_id=captain_profile_id,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(team)
                    else:
                        team.name = team_name
                        team.division = division_from_meta
                        team.category = competition_division
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

                    for m in data.get("riders", []):
                        profile_id_source = m.get("zid") or m.get("zwid") or m.get("profileId")
                        correct_profile_id_int = safe_int(profile_id_source, default=None)
                        if correct_profile_id_int is None:
                            skipped_riders.append(f"Rider senza profileId valido in TRC {trc}")
                            continue
                        rider_id = f"{trc}/{correct_profile_id_int}"
                        rider = WTRL_Rider.query.filter_by(id=rider_id).first()
                        
                        zftp_val = safe_float(m.get("zftp"))
                        zftpw_val = safe_float(m.get("zftpw"))
                        zmap_val = safe_float(m.get("zmap"))
                        zmapw_val = safe_float(m.get("zmapw"))
                        riderpoints_val = safe_int(m.get("riderpoints"), default=0)
                        teams_val = safe_int(m.get("teams"), default=0)
                        appearances_round_val = safe_int(m.get("appearancesRound"), default=0)
                        appearances_season_val = safe_int(m.get("appearancesSeason"), default=0)

                        if not rider:
                            rider = WTRL_Rider(
                                id=rider_id, team_trc=trc, profile_id=correct_profile_id_int,
                                tmuid=m.get("tmuid") or None, name=m.get("name"), avatar=m.get("avatar") or None,
                                member_status=m.get("memberStatus"), signedup=m.get("signedup", False),
                                category=m.get("category"), zftp=zftp_val, zftpw=zftpw_val,
                                zmap=zmap_val, zmapw=zmapw_val, riderpoints=riderpoints_val,
                                teams=teams_val, appearances_round=appearances_round_val,
                                appearances_season=appearances_season_val, user_id=m.get("userId"),
                                created_at=datetime.utcnow()
                            )
                            db.session.add(rider)
                        else:
                            rider.team_trc = trc
                            rider.profile_id = correct_profile_id_int
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
                
                    db.session.commit()
                    time.sleep(1)

                except requests.exceptions.RequestException as e:
                    db.session.rollback()
                    logger.error(f"Error fetching TRC {trc_id} from API: {str(e)}", exc_info=True)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"SQLAlchemyError importing TRC {trc_id}: {str(e)}", exc_info=True)
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Critical error importing TRC {trc_id}: {str(e)}", exc_info=True)
            
            final_message = f"Import completato: {teams_saved} team, {riders_saved} riders salvati."
            if skipped_riders:
                final_message += f" Attenzione: {len(skipped_riders)} ciclisti saltati."
            
            import_status_data['progress'] = 100
            import_status_data['message'] = final_message
        
        finally:
            import_status_data['is_running'] = False


@admin_bp.route("/wtrl_import/import_teams", methods=["GET"])
@login_required
def import_wtrl_teams_and_riders_from_api():
    """Triggers the background task to import WTRL teams and riders."""
    if import_status_data.get('is_running', False):
        flash("Un'altra importazione è già in corso.", "warning")
        return redirect(url_for("admin_bp.wtrl_teams_page"))

    season_number = request.args.get("season", "18")
    
    # Start the background thread
    # We pass current_app._get_current_object() to give the thread access to the app context
    thread = threading.Thread(target=run_import_in_background, args=(current_app._get_current_object(), season_number))
    thread.daemon = True
    thread.start()
    
    # Redirect to the progress page
    return redirect(url_for("admin_bp.import_progress"))


@admin_bp.route("/wtrl_teams")
@login_required
def wtrl_teams_page():
    """Renders the WTRL Teams page, likely to display imported teams."""
    # This route will eventually fetch and display teams from the database.
    # For now, it just renders the template.
    return render_template("admin/wtrl_teams.html")