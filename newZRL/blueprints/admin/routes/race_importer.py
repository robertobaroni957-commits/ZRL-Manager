# newZRL/blueprints/admin/race_importer.py

import os
import requests
import time
import random
from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
from datetime import datetime
from newZRL import db
from newZRL.models.team import Team
from newZRL.models.wtrl_rider import WTRL_Rider
from newZRL.models.race_results import RaceResultsTeam, RaceResultsRider, RoundStanding

from ..bp import admin_bp

# --------------------------
# CONFIGURAZIONE COOKIE/API
# --------------------------
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------------------
# UTILS
# --------------------------
def normalize_name(s):
    """Normalizza i nomi per confronto robusto."""
    if not s:
        return ""
    s = s.strip().upper()
    # rimuovi prefissi comuni e doppio spazio
    s = s.replace("TEAM ", "").replace("  ", " ")
    return s

def ensure_wtrl_json_ready(season: str, class_id: str, race_number: int,
                           max_retries: int = 14, initial_delay: float = 3.0,
                           max_delay: float = 8.0):
    """
    Chiede l'endpoint WTRL e attende che ritorni 200.
    Ritorna (success, response) dove response è l'oggetto requests.Response (se success)
    o l'ultima Response / errore se fallisce.
    Usa exponential backoff + jitter per non stressare il server.
    """
    url = f"https://www.wtrl.racing/api/zrl/results/{season}/{class_id}/{race_number}"
    delay = initial_delay

    wtrl_cookies = {"Cookie": current_app.config["WTRL_API_COOKIE"]} # Get cookie within app context

    last_response = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, cookies=wtrl_cookies, timeout=30)
        except Exception as e:
            # rete/timeout: loggalo e ritenta
            current_app.logger.error(f"[ensure_wtrl_json_ready] attempt {attempt} network error: {e}")
            last_response = None
            # backoff with jitter
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        last_response = resp

        if resp.status_code == 200:
            # JSON pronto
            return True, resp

        if resp.status_code == 202:
            # Non pronto: aspetta e ritenta
            current_app.logger.info(f"[ensure_wtrl_json_ready] attempt {attempt} got 202 (not ready). Waiting {delay:.1f}s")
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        # Qualsiasi altro codice (403, 404, 500...) -> fallimento
        current_app.logger.error(f"[ensure_wtrl_json_ready] attempt {attempt} got HTTP {resp.status_code}")
        # se è HTML di redirect (login), lo mostriamo per debug
        current_app.logger.debug(resp.text[:800])
        return False, resp

    # Se abbiamo esaurito i retry
    return False, last_response

def ensure_wtrl_league_json_ready(season: str, class_id: str, race_number: int,
                                  max_retries: int = 14, initial_delay: float = 3.0,
                                  max_delay: float = 8.0):
    """
    Chiede l'endpoint WTRL League e attende che ritorni 200.
    Ritorna (success, response) dove response è l'oggetto requests.Response (se success)
    o l'ultima Response / errore se fallisce.
    Usa exponential backoff + jitter per non stressare il server.
    """
    url = f"https://www.wtrl.racing/api/zrl/league/{season}/{class_id}/{race_number}"
    delay = initial_delay

    wtrl_cookies = {"Cookie": current_app.config["WTRL_API_COOKIE"]} # Get cookie within app context

    last_response = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, cookies=wtrl_cookies, timeout=30)
        except Exception as e:
            # rete/timeout: loggalo e ritenta
            current_app.logger.error(f"[ensure_wtrl_league_json_ready] attempt {attempt} network error: {e}")
            last_response = None
            # backoff with jitter
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        last_response = resp

        if resp.status_code == 200:
            # JSON pronto
            return True, resp

        if resp.status_code == 202:
            # Non pronto: aspetta e ritenta
            current_app.logger.info(f"[ensure_wtrl_league_json_ready] attempt {attempt} got 202 (not ready). Waiting {delay:.1f}s")
            time.sleep(min(max_delay, delay) + random.uniform(0, 0.5))
            delay = min(max_delay, delay * 1.8)
            continue

        # Qualsiasi altro codice (403, 404, 500...) -> fallimento
        current_app.logger.error(f"[ensure_wtrl_league_json_ready] attempt {attempt} got HTTP {resp.status_code}")
        # se è HTML di redirect (login), lo mostriamo per debug
        current_app.logger.debug(resp.text[:800])
        return False, resp

    # Se abbiamo esaurito i retry
    return False, last_response


# --------------------------
# ROUTE IMPORT GARA
# --------------------------
@admin_bp.route("/wtrl_import/import_rankings", methods=["GET"])
@login_required
def import_wtrl_rankings_from_api():
    """Importa o aggiorna le classifiche WTRL direttamente dall'API."""
    season_name = request.args.get("season", "17") # Default season 17
    race_number_arg = request.args.get("race_number") # Can be specific race number or None
    competition_class_arg = request.args.get("class_id") # This is now competition_class

    if not season_name.isdigit():
        flash("Numero stagione non valido", "error")
        return redirect(url_for("admin_bp.wtrl_rankings_page"))
    season_name = int(season_name)

    # Determine which competition_classes to import (always get all unique for the season)
    competition_classes_to_import = []
    # Get all unique competition_class from existing teams for this season
    unique_classes = db.session.query(Team.competition_class).filter(
        Team.competition_season == season_name,
        Team.competition_class.isnot(None)
    ).distinct().all()
    competition_classes_to_import = [c[0] for c in unique_classes]
    if not competition_classes_to_import:
        flash(f"Nessuna competition_class trovata per la stagione {season_name} nei team.", "warning")
        return redirect(url_for("admin_bp.wtrl_rankings_page"))

    # Determine which race numbers to import
    race_numbers_to_import = []
    if race_number_arg and race_number_arg.isdigit():
        race_numbers_to_import.append(int(race_number_arg))
    else:
        rounds = Round.query.filter_by(season_id=season_name).order_by(Round.round_number).all()
        if not rounds:
            flash(f"Nessun round trovato per la stagione {season_name}", "warning")
            return redirect(url_for("admin_bp.wtrl_rankings_page"))
        race_numbers_to_import = [r.round_number for r in rounds]
        if not race_numbers_to_import:
            flash(f"Nessun round trovato per la stagione {season_name} nel DB.", "warning")
            return redirect(url_for("admin_bp.wtrl_rankings_page"))
            
    total_teams_processed = 0
    total_races_imported = 0
    total_riders_imported = 0
    errors = []

    for race_num in race_numbers_to_import:
        for comp_class in competition_classes_to_import: # Use comp_class here



            processed_teams_for_this_segment = 0
            
            # Fetch results for this comp_class and race_num once
            ok, response = ensure_wtrl_json_ready(str(season_name), comp_class, race_num,
                                                max_retries=14, initial_delay=1.2, max_delay=8.0)

            if not ok:
                status = response.status_code if response is not None else "N/A"
                errors.append(f"Impossibile ottenere JSON WTRL per Season {season_name}, Class {comp_class}, Race {race_num} (HTTP {status})")
                if response is not None:
                    print(f"[import_rankings] RAW for Season {season_name}, Class {comp_class}, Race {race_num} (status {response.status_code}):")
                    print(response.text[:800])
                continue

            try:
                data = response.json()
            except ValueError:
                errors.append(f"Risposta non JSON ricevuta per Season {season_name}, Class {comp_class}, Race {race_num} anche dopo 200")
                print(response.text[:1000])
                continue

            if "payload" not in data or not isinstance(data["payload"], list):
                errors.append(f"Payload mancante o non array per Season {season_name}, Class {comp_class}, Race {race_num}")
                print("RAW payload:", data)
                continue

            payload = data["payload"]
            print(f"[import_rankings] Fetched payload with {len(payload)} team entries for Season {season_name}, Class {comp_class}, Race {race_num}")

            # Fetch league standings for this comp_class and race_num
            ok_league, response_league = ensure_wtrl_league_json_ready(str(season_name), comp_class, race_num,
                                                                       max_retries=14, initial_delay=1.2, max_delay=8.0)
            league_payload = []
            league_payload_map = {} # Map team_name to its league data for quick lookup
            if ok_league:
                try:
                    league_data = response_league.json()
                    if "payload" in league_data and isinstance(league_data["payload"], list):
                        league_payload = league_data["payload"]
                        for entry in league_payload:
                            team_name_from_league = entry.get("d") # 'd' is team name in league API
                            if team_name_from_league:
                                league_payload_map[normalize_name(team_name_from_league)] = entry
                except ValueError:
                    errors.append(f"Risposta non JSON ricevuta per League API per Season {season_name}, Class {comp_class}, Race {race_num}")
            else:
                status_league = response_league.status_code if response_league is not None else "N/A"
                errors.append(f"Impossibile ottenere JSON League API per Season {season_name}, Class {comp_class}, Race {race_num} (HTTP {status_league})")


            # Iterate through each team entry in the WTRL API payload
            for team_payload in payload:
                # Try to find team by trc or name, or create if not found
                team_trc_from_payload = team_payload.get("id5") or team_payload.get("id1")
                team_name_from_payload = team_payload.get("teamname")

                local_team = None
                if team_trc_from_payload:
                    local_team = Team.query.filter_by(trc=team_trc_from_payload).first()
                
                if not local_team and team_name_from_payload:
                    normalized_payload_name = normalize_name(team_name_from_payload)
                    local_team = Team.query.filter(
                        db.func.lower(Team.name) == db.func.lower(normalized_payload_name)
                    ).first()

                if not local_team:
                    # Create a placeholder team if not found
                    current_app.logger.info(f"[import_rankings] Team non trovato (TRC: {team_trc_from_payload}, Nome: {team_name_from_payload}). Creazione di un placeholder.")
                    local_team = Team(
                        trc=team_trc_from_payload,
                        name=team_name_from_payload,
                        division=team_payload.get("division"), # From payload
                        competition_class=comp_class, # Use current competition class
                        competition_season=season_name, # Use current season
                        # Other fields will be default or None
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(local_team)
                    db.session.flush() # Flush to get an ID for the new team

                # Now 'local_team' is guaranteed to be an actual Team object, existing or newly created.
                # All subsequent references to 'team' will use 'local_team'.
                team = local_team # Assign to 'team' variable for consistency with existing code

                time_result = team_payload.get("timeResult")

                # ----------------------
                # CREA RaceResultsTeam
                # ----------------------
                try:
                    # Check if result already exists and update
                    rrt = RaceResultsTeam.query.filter_by(
                        season=int(season_name),
                        class_id=comp_class,
                        race=race_num,
                        team_id=team.trc
                    ).first()

                    if not rrt:
                        rrt = RaceResultsTeam(
                            season=int(season_name),
                            class_id=comp_class,
                            race=race_num,
                            team_id=team.trc,
                            finp=int(team_payload.get("finp", 0)),
                            pbp=int(team_payload.get("pbp", 0)),
                            totp=int(team_payload.get("lpoints", 0)),
                            falp=int(team_payload.get("falp", 0)),
                            ftsp=int(team_payload.get("ftsp", 0)),
                            time_result=team_payload.get("timeResult"),
                            distance_result=team_payload.get("distanceResult"),
                            rank=int(team_payload.get("p1", 0)) # Corrected to use 'p1' for rank
                        )
                        db.session.add(rrt)
                    else:
                        rrt.finp=int(team_payload.get("finp", 0))
                        rrt.pbp=int(team_payload.get("pbp", 0))
                        rrt.totp=int(team_payload.get("lpoints", 0))
                        rrt.falp=int(team_payload.get("falp", 0))
                        rrt.ftsp=int(team_payload.get("ftsp", 0))
                        rrt.time_result=team_payload.get("timeResult")
                        rrt.distance_result=team_payload.get("distanceResult")
                        rrt.rank=int(team_payload.get("p1", 0)) # Updated to use 'p1' for rank

                    db.session.flush()  # per avere rrt.id
                    total_races_imported += 1 # Increment counter here

                except Exception as e:
                    db.session.rollback()
                    errors.append(f"Team {team.name} (TRC {team.trc}, Season {season_name}, Class {comp_class}, Race {race_num}): errore creando/aggiornando RaceResultsTeam -> {e}")
                    print("ERR create/update rrt:", e)
                    continue

                # ----------------------
                # CREA RaceResultsRider
                # ----------------------
                members = team_payload.get("a", []) or []
                for member in members:
                    rider_profile_id = member.get("zid") or member.get("p1") or ""
                    rider_profile_id = str(rider_profile_id)

                    if not rider_profile_id or rider_profile_id in ("0", "None"):
                        continue
                    
                    # Construct composite id for WTRL_Rider
                    # Assuming WTRL_Rider ID is trc/profile_id as defined in model
                    wtrl_rider_composite_id = f"{team.trc}/{rider_profile_id}" 

                    actual_rider = WTRL_Rider.query.filter_by(id=wtrl_rider_composite_id).first()
                    if not actual_rider:
                        # Rider not found, create a placeholder WTRL_Rider entry using ZID from race results
                        current_app.logger.info(f"[import_rankings] Rider non trovato in WTRL_Rider (ID: {wtrl_rider_composite_id}). Creazione di un placeholder.")
                        rider_name_from_ranking = member.get("name", f"Unknown Rider {rider_profile_id}")
                        rider_category_from_ranking = member.get("category", "") # Use category from race results payload if available

                        actual_rider = WTRL_Rider(
                            id=wtrl_rider_composite_id,
                            team_trc=team.trc,
                            profile_id=int(rider_profile_id), # Use the ZID from race results
                            name=rider_name_from_ranking,
                            category=str(rider_category_from_ranking),
                            # Other fields will be default or None
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.session.add(actual_rider)
                        db.session.flush() # Flush the new WTRL_Rider to make it visible



                    # Check if rider result already exists and update
                    rrr = RaceResultsRider.query.filter_by(
                        race_team_result_id=rrt.id,
                        rider_id=actual_rider.id
                    ).first()

                    if not rrr:
                        rrr = RaceResultsRider(
                            race_team_result_id=rrt.id,
                            rider_id=actual_rider.id,
                            finp=int(member.get("finrp", 0)),
                            pbp=int(member.get("pbprp", 0)),
                            totp=int(member.get("totrp", 0)),
                            falp=int(member.get("falrp", 0)),
                            ftsp=int(member.get("ftsrp", 0)),
                            time_result=member.get("timeResult"),
                            distance_result=member.get("distanceResult"),
                            wkg=float(member.get("wkg") or 0),
                            watts=float(member.get("watts") or 0),
                            gap=str(member.get("gap") or "0")
                        )
                        db.session.add(rrr)
                    else:
                        rrr.finp=int(member.get("finrp", 0))
                        rrr.pbp=int(member.get("pbprp", 0))
                        rrr.totp=int(member.get("totrp", 0))
                        rrr.falp=int(member.get("falrp", 0))
                        rrr.ftsp=int(member.get("ftsrp", 0))
                        rrr.time_result=member.get("timeResult")
                        rrr.distance_result=member.get("distanceResult")
                        rrr.wkg=float(member.get("wkg") or 0)
                        rrr.watts=float(member.get("watts") or 0)
                        rrr.gap=str(member.get("gap") or "0")
                    total_riders_imported += 1 # Increment counter here
                
                # ----------------------
                # AGGIORNA RoundStanding (per team e classe)
                # ----------------------
                try:
                    # Find corresponding team in league_payload_map
                    normalized_team_name = normalize_name(team.name)
                    league_entry = league_payload_map.get(normalized_team_name)

                    current_app.logger.info(f"[import_rankings] Processing RoundStanding for Team: {team.name} (TRC: {team.trc})")
                    current_app.logger.info(f"[import_rankings] Normalized Team Name: '{normalized_team_name}'")

                    if league_entry:
                        cumulative_total_points = int(league_entry.get("n", 0)) # 'n' field from league API is cumulative points
                        current_app.logger.info(f"[import_rankings] League Entry found. Cumulative Points (n): {cumulative_total_points}")
                        
                        rs = RoundStanding.query.filter_by(
                            season=int(season_name),
                            class_id=comp_class,
                            team_id=team.trc
                        ).first()

                        if not rs:
                            rs = RoundStanding(
                                season=int(season_name),
                                class_id=comp_class,
                                team_id=team.trc,
                                total_points=cumulative_total_points
                            )
                            db.session.add(rs)
                            current_app.logger.info(f"[import_rankings] Created RoundStanding for {team.name} with {cumulative_total_points} points.")
                        else:
                            rs.total_points = cumulative_total_points
                            rs.updated_at = datetime.utcnow()
                            current_app.logger.info(f"[import_rankings] Updated RoundStanding for {team.name} with {cumulative_total_points} points.")
                    else:
                        current_app.logger.warning(f"[import_rankings] Team {team.name} (TRC {team.trc}) (Normalized: '{normalized_team_name}') NOT FOUND in League API payload for Season {season_name}, Class {comp_class}, Race {race_num}. RoundStanding not updated, points may remain 0.")

                except Exception as e:
                    db.session.rollback()
                    errors.append(f"Errore aggiornando RoundStanding per team {team.name} (TRC {team.trc}, Season {season_name}, Class {comp_class}, Race {race_num}): {e}")
                    print(f"[import_rankings] errore aggiornando RoundStanding per team {team.name}: {e}")
            
            # Commit after processing all teams for a given race_num and comp_class
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                errors.append(f"Errore commit DB per Season {season_name}, Class {comp_class}, Race {race_num} -> {e}")
                print("ERR commit:", e)
                
            time.sleep(0.9) # Sleep breve per non sovraccaricare WTRL API
            time.sleep(1.0) # Additional sleep between competition classes to avoid 429 errors


    final_message = f"✅ Importazione completata per Stagione {season_name}: {total_races_imported} risultati gara team, {total_riders_imported} risultati rider importati/aggiornati."
    flash(final_message, "success")

    if errors:
        for err in set(errors): # Show unique errors
            flash(err, "error")

    return redirect(url_for("admin_bp.wtrl_rankings_page"))

# Existing routes for displaying standings (no change needed for now)
@admin_bp.route("/wtrl_rankings_page", methods=["GET"])
@login_required
def wtrl_rankings_page():
    seasons = db.session.query(RoundStanding.season).distinct().order_by(RoundStanding.season.desc()).all()
    
    selected_season = request.args.get('season', str(seasons[0][0]) if seasons else '')

    grouped_standings = {}
    if selected_season:
        all_standings_for_season = RoundStanding.query.filter_by(season=selected_season).order_by(
            RoundStanding.class_id, RoundStanding.total_points.desc()
        ).all()

        for standing in all_standings_for_season:
            if standing.class_id not in grouped_standings:
                grouped_standings[standing.class_id] = []
            grouped_standings[standing.class_id].append(standing)

    return render_template(
        "admin/wtrl_rankings.html", 
        seasons=seasons, 
        grouped_standings=grouped_standings, 
        selected_season=selected_season
    )

